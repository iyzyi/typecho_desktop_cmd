import re, os, requests
from urllib.parse import unquote
import post as P


def upload_pic(pic_name, name, url, token1, ip, user, password, database):    #上传一张图片（不包括修改所属parent）
    post = P.POST(url, token1, ip, user, password, database)
    post.login()
    r = post.upload_pic(pic_name, name)

    pic_dict = {}
    cid = re.search(r'"cid":"?(\d+)"?', r.text).group(1)
    pic_dict['cid'] = cid
    upload_path = re.search(r'(/usr\\/uploads\\/.+?)"', r.text).group(1).replace('\\','')
    pic_dict['upload_path'] = url + upload_path
    return pic_dict


def upload_pics(pic_list, url, token1, ip, user, password, database):
    #通过读取pic_list,上传多张图片（不包括修改所属parent）
    #pic_list内嵌套pic_dict，字典应有以下key：图片名称，本地路径，上传路径，图片cid，以及tag(就是![1](2)中2替代的字符串)
    post = P.POST(url, token1, ip, user, password, database)
    post.login()
    for pic_dict in pic_list:
        print(pic_dict['local_path'], pic_dict['name'])
        r = post.upload_pic(pic_dict['local_path'], pic_dict['name'])
        #print(r.text)
        '''
        回显形如：
        ["http:\/\/localhost\/blog2\/usr\/uploads\/2019\/09\/302509433.png",{"cid":38,"title":"1.png","type":"png","size":370995,"bytes":"363 Kb","isImage":true,"url":"http:\/\/localhost\/blog2\/usr\/uploads\/2019\/09\/302509433.png","permalink":"http:\/\/localhost\/blog2\/index.php\/attachment\/38\/"}]
        '''
        cid = re.search(r'"cid":"?(\d+)"?', r.text).group(1)
        pic_dict['cid'] = cid

        upload_path = re.search(r'(/usr\\/uploads\\/.+?)"', r.text).group(1).replace('\\','')
        pic_dict['upload_path'] = url + upload_path


def down_pic(url, path):    #从网络上下载图片
    print('####正在下载%s####'%url)
    r = requests.get(url)
    if len(str(r.content)) > 300:
        name = os.path.split(url)[1]
        pic_path = os.path.join(path, name)
        with open(pic_path, 'wb') as f:
            f.write(r.content)
        return pic_path
    else:
        print('####下载失败%s####'%url)


def add_pic_to_dict(pic_dict, pic_path, base_url, localDir, opera_own_pic=False):    #将提取出来的相关信息添加进dict
    try:    #尝试提取图片名称，如果提取失败，则说明正则提取出来的一定不是文件。虽然出错概率应该很小
        pic_name = os.path.split(pic_path)[1]
        pic_dict['name'] = pic_name
        if not pic_name:
            return None
    except:
        return None
    
    if re.search(r'^file:///(.+?)', pic_path):    #如果路径以file:///开头，则删掉file:///。此情景针对于有道云笔记的部分
        pic_path = re.search(r'^file:///(.+)', pic_path).group(1)
    
    if re.search(r'^[a-zA-Z]:(\\|/)', pic_path):   #本地图片
        pic_dict['local_path'] = pic_path
        
    elif re.search(r'^https?://', pic_path):    #网络图片
        url = pic_path
        #print(1111111222222,url)
        
        if re.search('^%s/usr/uploads/'%base_url.replace('.','\\.'), pic_path):    #本站的网络图片
            if opera_own_pic:
                dir_path = os.path.join(localDir, 'pic')
                if not os.path.exists(dir_path):
                    os.makedirs(dir_path)
                pic_path = down_pic(url, dir_path)
                pic_dict['local_path'] = pic_path
        
        else:    #非本站的网络图片
            dir_path = os.path.join(localDir, 'pic')
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
            pic_path = down_pic(url, dir_path)
            pic_dict['local_path'] = pic_path
    
    return pic_dict
    

def find_pics(text, base_url, localDir, opera_own_pic=False):    
    '''
    本函数只负责寻找所有符合条件的图片，并形成list。!!!顺便把扫到的网络图片下载到本地!!!
    图片有三种，
    本地图片，直接上传
    非本站(base_url不是本站url)的网络图片，先下载到本地，再上传
    本站的网络图片，opera_own_pic为False时，忽略此类图片，opera_own_pic为True，和非本站的网络图片当成一类。
    '''
    
    pic_list = []    #内置字典参数，字典应有以下key：图片名称，本地路径，上传路径, 图片cid，以及tag(就是![1](2)中2替代的字符串
    '''形如
    ![img](file:///C:/Users/e115fa0150ae49f2bb3cdc67d6095e41/clipboard.png)
    ![img](C:/Users/1366a9d20da5475cbd23da5bac1fa3fa/clipboard.png)
    '''
    '''
    发现了一个毒瘤哎，图片名称里含有括号
    ![](D:\图片\喜欢\超喜欢(54图)_@越半月圆收集_花瓣美女1281828885.jpg)
    正则拿到的路径是D:\图片\喜欢\超喜欢(54图
    先不管了，加上个图片上传失败则跳过此图片吧
    
    已解决19.09.07
    '''
    pic_iter = re.finditer(r'\!\[(.*?)\]\((.*?\.(jpg|png|gif|bmp|png))\)', text)
    for tag in pic_iter:
        pic_dict = {}
        pic_dict['tag'] = tag.group(2)
        pic_path = unquote(tag.group(2))    #图片名称含有汉字时，有道云笔记采用url编码的方式来记录，所以解码找到对应的图片位置。其他情形可能存在bug。
        
        pic_dict = add_pic_to_dict(pic_dict, pic_path, base_url, localDir, opera_own_pic)
        if pic_dict:
            #print('okokok')
            #除了一些markdown插入图片语句写错的情况外，正常来说，只有一种情况是没有键'local_path'的,
            #那就是图片是本站图片，且opera_own_pic为False，此时由于不需要上传图片，所以不需要将字典压入pic_list
            if 'local_path' in pic_dict:
                #print('sdsdfsdfs')
                pic_list.append(pic_dict)

    '''形如
    ![abc][1]
    [1]: http://blog.fatiger.cn/usr/uploads/2019/07/2363848679.jpg
    此为md进阶用法，由于我写md时从来不用此语法，唯一需要的就是typecho在web插入图片时会采用这种语法，
    所以下面按照typecho的格式来解析，就不严格写了，能对于typecho在web插入的图片解析正确就足够了
    你们如果习惯用此md语法，请自行添加语句（主要是标签关键字的正确字符格式以及各[]之间的空格对于解析结果的影响）
    '''
    
    num_iter = re.finditer(r'\!\[.*?\]\[(\d+)\]', text)
    num_list = list(num_iter)    #第一次知道迭代器只能迭代一次，需要转成list才能迭代多次
    tag_iter = re.finditer(r'\[(\d+)\]: ?(.*?\.(jpg|png|gif|bmp|png))[\n\r]', text)
    tag_list = list(tag_iter)
    for num in num_list:
        pic_dict = {}
        for tag in tag_list:
            #print(num.group(1),222222222,tag.group(1))
            if num and tag and num.group(1) == tag.group(1):
                pic_dict['tag'] = tag.group(2)    #图片地址
                #print(22222222222222,pic_dict['tag'])
                pic_path = tag.group(2)
                break
        if 'tag' in pic_dict:    
            pic_dict = add_pic_to_dict(pic_dict, pic_path, base_url, localDir, opera_own_pic)
        #print(11111111111,pic_dict)
        if pic_dict:
            if 'local_path' in pic_dict:
                pic_list.append(pic_dict)
    
    num_iter = re.finditer(r'\!\[.*?\]\[(\d+)\]', text)
    num_list = list(num_iter)
    tag_iter = re.finditer(r'\[(\d+)\]: ?(.*?\.(jpg|png|gif|bmp|png))[\n\r]*$', text)   #匹配文末的那张图片
    tag_list = list(tag_iter)
    for num in num_list:
        pic_dict = {}
        for tag in tag_list:
            #print(num, tag, num.group(1), tag.group(1))
            if num and tag and num.group(1) == tag.group(1):
                #print('hhhhhhhhhhhhha')
                pic_dict['tag'] = tag.group(2)    #图片地址
                #print(pic_dict)
                #print(22222222222222,pic_dict['tag'])
                pic_path = tag.group(2)
                break    
        if 'tag' in pic_dict:
            pic_dict = add_pic_to_dict(pic_dict, pic_path, base_url, localDir, opera_own_pic)
        #print(11111111111,pic_dict)
        if pic_dict:
            if 'local_path' in pic_dict:
                pic_list.append(pic_dict)

    
    #print(pic_list)
    return pic_list


if __name__ == '__main__':
    
    url = 'http://localhost/blog2'
    token1 = 'IEqbi2CiS5UrOlKtFRMzTQ)S2)G33EFd'
    ip = '127.0.0.1'
    user = 'root'
    password = 'root'
    database = 'blog2'

    #pic_dict = {'name': '1.png', 'local_path':r'D:\图片\喜欢\超喜欢(54图)_@越半月圆收集_花瓣美女1281828885.jpg'}
    #pic_list = [pic_dict]
    #upload_pics(pic_list, url, token1, ip, user, password, database)
    with open(r'D:\计算机\Project\typecho_desktop_cmd\md\ida远程调试linux程序——阿里云CentOS版.md','r',encoding='utf-8')as f:
        text = f.read()
    p = find_pics(text, 'http://iyzy.xyz', r'D:\计算机\Project\typecho_desktop_cmd', opera_own_pic=False)
    for i in p:
        print(i['tag'])