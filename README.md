这个代码也是写了好久好久，就上传到github上留念一下，纪念自己的热血吧

具体程序逻辑请参考下图

![](逻辑流程图.png)

使用方法请参考module.py文件的EventProcessor类，里面有例子

如果你只需要结果，则只需要实例化EventProcessor，然后调用内置的添加角色函数，即可获得结果

目前来说，如果你需要分段运行，则需要参照EventProcessor类中run函数里的流程，依次调用gameStart、turnStart、move、gameEnd流程进行，然后在中间自主加入读取EventData以进行其他操作