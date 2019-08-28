print("-" * 10 + "方法1" + "-" * 10)


# 方法1， 实现__new__ 方法
# 将这个类的唯一实例绑定到类变量_instance 上，
# 如果cls.instance 为 None 说明该类还没有实例化过，进行实例化，并返回
# 如果cls.instance 不为 None ，直接返回 cls._instance

class Singleton(object):
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            orig = super(Singleton, cls)
            cls._instance = orig.__new__(cls, *args, **kwargs)
        return cls._instance


# test 创建自己的类继承自单例模式类
class MyClass(Singleton):
    a = 1


one = MyClass()
two = MyClass()

print(id(one))
print(id(two))

print("-" * 10 + "方法2" + "-" * 10)


# 方式2， 共享属性法；所谓单例就是所有引用的实例都拥有相同的属性和方法
# 同一个类的所有实例天然拥有相同的方法，此时只需要确保同一个类的所欲实例都具有相同的属性即可
# 实现方式是 将__dict__ 属性指向同一个字典
# 注意：此实现是一种伪单例， 实现是创建出了多个对象，只是对象的 __dict__ 是指向同一个字典

class Borg(object):
    _state = {}

    def __new__(cls, *args, **kwargs):
        ob = super(Borg, cls).__new__(cls, *args, **kwargs)
        ob.__dict__ = cls._state
        return ob


class MyClass2(Borg):
    a = 1


one = MyClass2()
two = MyClass2()

print(id(one.__dict__))
print(id(two.__dict__))

one.__dict__["test"] = "hahah"
print(two.__dict__["test"])

print("-" * 10 + "方法3" + "-" * 10)


# 方法3：本质上是方法1的升级版
# 使用 __metaclass__ （元类）的高级用法
class Singleton3(type):
    def __call__(cls, *args, **kw):
        if not hasattr(cls, "_instance"):
            cls._instance = super().__call__(*args, **kw)
            return cls._instance
        return cls._instance


class MyClass3(metaclass=Singleton3):
    a = 1


one = MyClass3()
two = MyClass3()

print(id(one))
print(id(two))

print(one.a)
print(two.a)


# 方法4 : 最简单的方法， 类的静态方法
class Singleton4():
    __instance = None

    @staticmethod
    def getInstance():
        if Singleton4.__instance == None:
            Singleton4.__instance = Singleton4()
        return Singleton4.__instance




one = Singleton4.getInstance()
two = Singleton4.getInstance()
print(id(one))
print(id(two))
print(one)

