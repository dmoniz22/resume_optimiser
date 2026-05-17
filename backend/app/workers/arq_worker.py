from arq.worker import Worker


async def startup(ctx):
    pass


async def shutdown(ctx):
    pass


async def health_check(ctx) -> dict:
    return {"status": "ok", "worker": "resume_optimizer"}


class WorkerSettings:
    functions = [health_check]
    redis_settings = {
        "host": "valkey",
        "port": 6379,
        "database": 0,
    }
    on_startup = startup
    on_shutdown = shutdown
