# 判断出现网络无法训练的原因是`Tri`出现了训练瓶颈。并且因为`Tri`和`交叉熵`损失函数在一前一后，所有导致`交叉熵`的训练优化效果也失效。

# 所以，本次实验的目的是交换`Tri`和`交叉熵`的计算先后顺序。

# 但实际上是因为，在网络中我过度使用非线性激活函数`ReLU`所导致。问题已经解决。