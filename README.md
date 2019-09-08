## 功能

1　下载文章（不下载图片，适用于修改文章后再次上传）

2　下载文章（下载全部图片，适用于本地的备份）

3　下载文章（图片以base64形式写入md文件，便于分享）　#TODO

4　上传全新文章（数据库中不存在）

5　上传修改文章（数据库中存在）

6　删除文章

7　移动文章（所属分类）

8　创建分类

9　下载全部文章（包括全部图片）

## 依赖

requests，pymysql

## 实现思路

对于大部分操作，都是通过pymysql直接对数据库进行远程操作，但是图片的上传和创建目录是通过post传值的方式实现的。图片上传为了安全考虑，没有通过ftp传输；而创建目录是因为数据库的typecho_metas表中的order列无法进行数据修改，迫不得已。

原来想做GUI的，后来不耐烦了，鸽了。先将就用吧。寒假我打算写个笔记软件，到时候顺便将这个需求直接整合到笔记软件上吧，就不额外写了。

## 一些弯路

我一开始想全部通过数据库修改实现，但后来脑子转过弯来了，醒悟若真这么做了，岂不是相当于自己写了python的后端？？

最简单的做法，应该是能通过post传的就用post传，这样只需要将数据提交，数据库的写入由网站的后端操作，可以避免自己写的数据库操作出bug。而对于数据入库后的信息，比如新建文章的cid，可以自己用pymysql获取具体的值。二者相结合，效率更高，bug也会少很多。

然而还是醒悟晚了，导致我看我的程序，简直就像看shit一样。。。

## 文件介绍

**operation.py** 程序入口，操作都在这里面进行

**PyMySQL.py** 对数据库的增删改查进行针对性的封装

**post.py** post传值

**pic.py** 有关图片的操作

**blogs_settings.py** 配置文件

## 使用前必做

typecho是带有token的，token由四部分组成，分别为长度为32的字符串（建站时初始化，之后不变），长度为32的字符串authCode（每次登录时随机化），user的id，一般admin为1，具体页面的referer。四部分以&连接，然后md5作为token。（代码在\var\Widget\Security.php，可自己去看一下）

我们需要手动获取token1，token2和3连接数据库后程序自动获取，token4也已经写在程序里了，所以只需要获取token1

### 获取token1

搭建typecho一般都用宝塔吧，当然这不重要，只要你能用自己的方式打开网址目录下的`\var\Widget\Security.php`就行。

打开后，找到

```php
public function execute()
{
    $this->_options = $this->widget('Widget_Options');
    $user = $this->widget('Widget_User');

    $this->_token = $this->_options->secret;
    if ($user->hasLogin()) {
    $this->_token .= '&' . $user->authCode . '&' . $user->uid;
    }
}
```

添加`echo "<script>alert('提示内容')</script>";`,如下：

```php
public function execute()
{
    $this->_options = $this->widget('Widget_Options');
    $user = $this->widget('Widget_User');

    $this->_token = $this->_options->secret;
    echo "<script>alert('$this->_token')</script>";
    if ($user->hasLogin()) {
    $this->_token .= '&' . $user->authCode . '&' . $user->uid;
    }
}
```

然后打开你的博客，刷新一下，会弹出一个窗口，文本内容就是token1。

**最后不要忘记删掉刚刚我们添加的那条语句**

### 开启数据库远程连接

[我整理的一篇相关的文章，仅供参考](http://iyzy.xyz/index.php/archives/449/)

### 程序配置

**blogs_settings.py**可以设置你的博客配置信息，配置信息包括必填和选填两部分。

打开**blogs_settings.py**后， 你会发现注释中写的很清楚了，这里我在补充几点：

1、必填中的url和token是为了post传值，ip,user,password,database是数据库的配置信息

2、如果你有多个typecho博客，可以添加多个博客的配置信息

3、注意，配置信息的添加不是覆盖，而是追加，当添加了错误的信息时，请先删除生成的**typecho.conf **，否则错误的信息会一直在**typecho.conf **中。

4、使用不同的typecho模板会设定不同的自定义字段（我说的不是你自己添加的自定义字段，而是你使用的外观模板的作者设定的自定义字段），体现在你写博客的那个界面的文本框的下方。如果你实在不会下面的操作，或是没有这个需求，可以忽略这一步。

自定义字段的相关信息在表typecho_fields中，查看前你要先在web端写一篇使用到所有的外观模板的作者设定的自定义字段的文章（“的”比较多，泥萌好好断句）。

```
mysql -uroot -p123456
#123456替换成你的数据库root密码

use blog
#blog替换成你的typecho数据库名称

select * from typecho_fields;
#此时你可以看到相关的自定义字段了
```

![1567582430893](https://github.com/iyzyi/typecho_desktop_cmd/blob/master/pic/1567582430893.png?raw=true)

name填写图中类似thumbnail的字符串（我这里的thumbnail,previewContent等都是我使用的外观模板的作者设定的，你的可能会和我的不同。而且注意，必须你写过的文章中使用过这些自定义字段，数据库中才会显示）

type就写对应的类型，str，int，float三种

detail就写 程序运行到需要你输入自定义字段的时候，你希望程序会输出什么来提示你。

比如说，我的thumbnai这个字段是控制文章封面的，所以detail我写的`detail = '封面图片：'`

## 运行

全部设置好之后，就可以使用**opration.py**了

部分运行截图

![1567582946346](https://github.com/iyzyi/typecho_desktop_cmd/blob/master/pic/1567582946346.png?raw=true)

![1567582999459](https://github.com/iyzyi/typecho_desktop_cmd/blob/master/pic/1567582999459.png?raw=true)

比较丑啊，希望别见怪，毕竟我是直男本男。。

如果你不想输出mysql的操作语句，可以在operation.py中修改print_sql为False。

## 已知bug

`![](D:\图片\喜欢\ゞ静侞処Ζīoо(1905图)_@sZmnRcdI收集_花瓣美女907377431.jpg)`

图片名称中含有（），导致正则匹配不到正确的图片地址，实在想不到解决的方案

## 时间线

20190904　　第一次上传

20190908　　

* 修复图片名称不能含（）的问题
* 修复更新文章时新上传的图片未归档的问题
* 修改update的sql语句不输出的问题
* 对于功能2下载的md文件，图片的本地地址由绝对路径改为相对路径

* 增添下载全部文章（包括全部图片）的功能，替换掉原有的TODO的功能9删除目录（鸡肋）。此功能极其适合备份，其中图片的路径为相对路径。拷贝时顺带着拷贝pic文件夹即可。

20190909　　修复上传数据库时，反斜杠会转义后一位字符（解决方案：上传前单个反斜杠替换成两个反斜杠）