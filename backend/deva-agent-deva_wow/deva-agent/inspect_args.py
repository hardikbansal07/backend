import inspect
from kerykeion import AstrologicalSubject

sig = inspect.signature(AstrologicalSubject.__init__)
print(sig)
