这个代码也是写了好久好久，就上传到github上留念一下，纪念自己的热血吧
具体程序逻辑请参考下图
![](逻辑流程图.png)
使用方法请参考module.py文件的EventProcessor类，里面有例子
如果你只需要结果，则只需要实例化EventProcessor，然后调用内置的添加角色函数，即可获得结果
注：run函数返回的不是可阅读数据，需要调用resultToNameDict以转成可阅读数据，不过未来可能会更改
