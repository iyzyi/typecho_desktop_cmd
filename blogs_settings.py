import json, os


'''
生成的json转换为python数据的话，数据结构是这样的：
转换后得到一个列表，列表内嵌套着两个列表，
第一个列表为blogs登录及数据库登录，内部嵌套字典，字典有url,token1,ip,user,password,database,localDir的键
第二个列表为自定义字段，内部嵌套字典，字典有name, type, value的键
示例见最后
'''

def add_blogs(url, token1, ip, user, password, database, localDir):    #添加博客信息，可添加多次，这样可以在不同的博客中切换
    if os.path.exists('typecho.conf'):
        with open('typecho.conf') as f:
            file = f.read()
        conf_list = json.loads(file)
        user_list = conf_list[0]
    else:
        conf_list = []
        user_list = []
        field_list = []
        conf_list.append(user_list)
        conf_list.append(field_list)
    user_dict = {}
    user_dict['url'] = url
    user_dict['token1'] = token1
    user_dict['ip'] = ip
    user_dict['user'] = user
    user_dict['password'] = password
    user_dict['database'] = database
    user_dict['localDir'] = localDir
    user_list.append(user_dict)
    
    conf_list[0] = user_list
    conf_json = json.dumps(conf_list, sort_keys=True, indent=4, separators=(',', ':'))
    with open('typecho.conf', 'w') as f:
        f.write(conf_json)
        

def add_field(name, type, detail):    #自定义字段
    with open('typecho.conf') as f:
        file = f.read()
    conf_list = json.loads(file)
    field_list = conf_list[1]
    field_dict = {}
    field_dict['name'] = name
    field_dict['type'] = type
    field_dict['detail'] = detail
    field_list.append(field_dict)
    
    conf_list[1] = field_list
    conf_json = json.dumps(conf_list, sort_keys=True, indent=4, separators=(',', ':'))
    with open('typecho.conf', 'w') as f:
        f.write(conf_json)    
        

if __name__ == '__main__':
    
    #注意，下次运行此程序前先看看是否有之前添加过一次的信息，小心重复添加。
    #比如自定义字段，曾经添加过了的字段，就不要重复添加了。


    #必填
    
    url = 'http://localhost/blog2'    #博客的url，可以是外网url，也可以是内网url，含http(s)://，最后一个字符不为/
    token1 = 'IEqbi2CiS5UrOlKtFRMzTQ)S2)G33EFd'    #token的一部分来源，具体请看README.md中的介绍
    ip = '127.0.0.1'    #服务器的ip，连接数据库用
    user = 'root'    #mysql用户名
    password = 'root'    #mysql密码
    database = 'blog2'    #typecho博客所用的数据库
    localDir = r'D:\计算机\Project\typecho_desktop_beifen\md'    #下载博客文章到本地时的路径
    add_blogs(url, token1, ip, user, password, database, localDir)
    
        
    
    #选填，作用是自定义字段（不同的typecho的主题会用到不同的自定义字段），具体请看README.md中
    
    name = 'thumbnail'
    type = 'str'
    detail = '封面图片：'
    add_field(name, type, detail)
    
    name = 'previewContent'
    type = 'str'
    detail = '预览文字：'
    add_field(name, type, detail)
    
    name = 'showTOC'
    type = 'str'
    detail = '是否开启h2,h3标题解析（1为开启，0为关闭）：'
    add_field(name, type, detail)
    
    
    
    
    
    
    
'''生成的json示例
[
    [
        {
            "database":"blog2",
            "ip":"127.0.0.1",
            "localDir":"D:\\\u8ba1\u7b97\u673a\\Project\\typecho_desktop_beifen\\md",
            "password":"root",
            "token1":"IEqbi2CiS5UrOlKtFRMzTQ)S2)G33EFd",
            "url":"http://localhost/blog2",
            "user":"root"
        }
    ],
    [
        {
            "name":"thumbnail",
            "type":"str",
            "value":"\u5c01\u9762\u56fe\u7247\uff1a"
        },
        {
            "name":"previewContent",
            "type":"str",
            "value":"\u9884\u89c8\u6587\u5b57\uff1a"
        },
        {
            "name":"showTOC",
            "type":"str",
            "value":"\u662f\u5426\u5f00\u542fh2,h3\u6807\u9898\u89e3\u6790\uff081\u4e3a\u5f00\u542f\uff0c0\u4e3a\u5173\u95ed\uff09\uff1a"
        }
    ]
]
'''