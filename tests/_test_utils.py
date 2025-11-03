def mock_args(return_val=None, _is_exp=False):
    def mock(*args, **kwargs):
        if _is_exp:
            raise return_val
        return return_val

    return mock


def mock_args_async(return_val=None, _is_exp=False):
    async def mock(*args, **kwargs):
        if _is_exp:
            raise return_val
        return return_val

    return mock


def mock_execute(executable_func, _is_sync=False):

    async def mock_exec(*args, **kwargs):
        # directly execute the function
        if _is_sync:
            return executable_func(*args, **kwargs)
        return await executable_func(*args, **kwargs)

    return mock_exec
