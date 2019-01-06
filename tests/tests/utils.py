from typing import Callable


class NotImplementedMixin:
    def assertNotImplemented(self, func: Callable, *args, **kwargs) -> None:
        try:
            func(*args, **kwargs)
        except AssertionError as exc:
            print("NOT IMPLEMENTED:", self.id(), exc)
        else:
            raise AssertionError("Function Implemented successfully!!")

    def assertNotImplementedNotEqual(self, *args, **kwargs):
        self.assertNotImplemented(self.assertNotEqual, *args, **kwargs)
