### 1. 案例背景与现象
+ **项目背景**：某 Spring Boot 工程从 JDK 8 升级至 JDK 17，FreeMarker 依赖随spring版本升级至 2.3.32。
+ **故障场景**：一个使用 `CompletableFuture` 进行异步处理的接口，在读取 `resources/templates/ftl` 下的模板文件时报错。
+ **报错特征**：
    - 控制台出现 `concurrent` 相关异常堆栈。
    - 提示 FreeMarkerLoader 加载失败，未指定目标文件相对路径。
    - 异步线程的 ClassLoader 显示为 `loader2`（非主线程的 `LaunchedURLClassLoader`）。
    - 伴随 `InaccessibleObjectException` 或反射访问属性失败的报错。
+ **临时解决**：通过自定义异步线程 Executor 替代默认线程池后问题解决，但需探究底层原理。

#### 2. 根因分析
本次故障并非单一问题，而是 **JDK 9+ 模块化系统（JPMS）** 与 **JDK 17 并发基础设施变更** 叠加导致的故障。

##### 2.1 核心原因一：TCCL（线程上下文类加载器）丢失
+ **JDK 8 行为**：`ForkJoinPool.commonPool()` 的工作线程通常继承主线程的 TCCL（即 `AppClassLoader`），FreeMarker 通过 `Thread.currentThread().getContextClassLoader()` 可正常定位 classpath 资源。
+ **JDK 17 变更**：引入 JPMS 后，类加载器层级增加 `PlatformClassLoader`。出于安全与模块隔离考虑，`commonPool` 作为 JVM 基础设施级线程池，其工作线程的 TCCL **不再保证继承应用类加载器**，可能被重置为系统类加载器或平台类加载器。
+ **后果**：FreeMarker 在异步线程中使用了错误的 ClassLoader，导致无法看到应用内部的 `resources/templates` 路径。

##### 2.2 核心原因二：JPMS 强封装导致反射拦截
+ **历史遗留**：FreeMarker 等框架深度依赖 `setAccessible(true)` 访问私有字段/方法以渲染模板。
+ **JDK 17 强制生效**：JEP 403 将强封装从警告升级为默认强制行为。当 `commonPool` 线程尝试反射访问未 `opens` 的模块内部 API 时，直接抛出 `InaccessibleObjectException`。
+ **叠加效应**：TCCL 错误可能导致 FreeMarker 回退到需要更多反射权限的代码路径，而反射被拦截又导致 BeansWrapper 初始化失败，最终表现为模板加载异常。

##### 2.3 为什么自定义 Executor 能同时解决两个问题？
自定义 `ThreadPoolTaskExecutor` 创建的线程属于“应用级执行环境”：

1. **TCCL 正确继承**：新线程默认继承父线程（业务线程）的 TCCL，确保拥有正确的 `LaunchedURLClassLoader`。
2. **反射权限完整**：作为无名模块的一部分，应用线程对应用类享有完整反射权限，不受 `commonPool` 的基础设施级安全限制。

#### 3. 关键知识点延伸
##### 3.1 JPMS (Java Platform Module System) 核心影响
| 维度 | JDK 8 | JDK 17 | 对业务的影响 |
| --- | --- | --- | --- |
| 代码组织 | 扁平 jar 包集合 | module-info.java 显式声明边界 | 需检查第三方库模块化兼容性 |
| 访问控制 | public 即可反射 | 必须 exports + opens 才能反射 | 老框架可能报 InaccessibleObjectException |
| 类加载器 | Bootstrap → App | Bootstrap → Platform → App | TCCL 行为变更，资源加载路径变化 |


##### 3.2 commonPool 使用决策矩阵（JDK 17+）
| 场景 | 是否可用 commonPool | 说明 |
| --- | --- | --- |
| 纯 CPU 计算（无 I/O、无第三方库） | ✅ 可以 | 如 `parallelStream`<br/> 纯内存聚合 |
| 涉及 I/O、网络、DB | ❌ 禁止 | 线程数少，阻塞会导致全局饥饿 |
| 使用 Spring Bean / 模板引擎 / ORM | ❌ 禁止 | TCCL 与反射权限均不满足 |
| 需要 MDC / TraceId / Security 上下文传播 | ❌ 禁止 | commonPool 不支持自动上下文传递 |
| 需要监控、告警、独立生命周期管理 | ❌ 禁止 | 基础设施池无法接入企业监控体系 |


**核心认知升级**：JDK 17 的 `commonPool` 已从“通用工具池”退化为“JVM 内部基础设施池”。在业务代码中应将其视为“不存在”，始终使用自定义 Executor。

#### 4. 解决方案与最佳实践
##### 4.1 必做项
1. **显式配置异步线程池**：

```java
@Bean("businessAsyncExecutor")
public Executor businessAsyncExecutor() {
    ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
    executor.setCorePoolSize(10);
    executor.setMaxPoolSize(50);
    executor.setQueueCapacity(200);
    executor.setThreadNamePrefix("biz-async-");
    // 关键：装饰器确保 TCCL + MDC + Security 上下文正确传播
    executor.setTaskDecorator(new ContextCopyingDecorator());
    executor.initialize();
    return executor;
}
```

2. **FreeMarker 显式绑定 ClassLoader**（消除对运行时 TCCL 的隐式依赖）：

```java
Configuration cfg = new Configuration(Configuration.VERSION_2_3_32);
cfg.setClassLoaderForTemplateLoading(
    YourApplication.class.getClassLoader(), 
    "/templates/ftl"
);
```

##### 4.2 兜底项（仅用于迁移期或无法修改代码时）
若确实遇到 JPMS 反射拦截，可通过 JVM 参数临时放行：

```bash
--add-opens java.base/java.lang=ALL-UNNAMED
--add-opens java.base/java.util=ALL-UNNAMED
```

⚠️ **注意**：此参数破坏 JPMS 安全模型，应视为技术债并创建 TODO 跟踪移除计划。

##### 4.3 诊断工具
+ `-Xlog:class+module=debug`：打印模块解析与开放决策，精确定位反射拦截点。
+ `jdeps --jdk-internals -R --class-path 'libs/*' your-app.jar`：分析 jar 包对 JDK 内部 API 的依赖。

#### 5. 参考资料
1. [JEP 261: Module System (Class Loader Hierarchy)](https://openjdk.org/jeps/261#Class-loaders) - 官方定义 JDK 9+ 类加载器层级变更
2. [JEP 403: Strongly Encapsulate JDK Internals](https://openjdk.org/jeps/403) - JDK 17 强封装强制生效规范
3. [JDK-8172726: ForkJoinPool common pool TCCL issues](https://bugs.openjdk.org/browse/JDK-8172726) - OpenJDK 官方 Issue，记录 commonPool TCCL 行为变更
4. [FreeMarker Official: ClassTemplateLoader](https://freemarker.apache.org/docs/api/freemarker/cache/ClassTemplateLoader.html) - FreeMarker 对 TCCL 依赖性及显式配置推荐
5. [Spring Boot 3 Migration Guide: Async & Reflective Access](https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-3.0-Migration-Guide) - Spring 官方迁移指南中线程池与反射兼容性章节
6. [Baeldung: CompletableFuture and Custom Executors in Java 17](https://www.baeldung.com/java-completablefuture-custom-executor) - JDK 8 vs 17 默认执行器行为差异详解

## 🏷️ 标签
#java #jdk #jvm #spring-boot #concurrency#jpms

