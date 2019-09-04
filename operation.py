import pic
import post as P
import PyMySQL as PM
import time, os, re, json


class Typecho():

    def __init__(self, user_dict):
        self.url = user_dict['url']
        self.token1 = user_dict['token1']
        self.ip = user_dict['ip']
        self.user = user_dict['user']
        self.password = user_dict['password']
        self.database = user_dict['database']
        self.localDir = user_dict['localDir']
        if not os.path.exists(self.localDir):
            os.makedirs(self.localDir)
        
        self.db = PM.DB(ip=self.ip, user=self.user, password=self.password, database=self.database, print_sql=True)

    
    def get_category(self):    #获取所有分类
        category = self.db.select('typecho_metas', 'mid', 'name', 'parent', type='"category"')
        return category
        '''形如
        ((1, '计算机', 0), (2, '诗词', 0), (3, 'CTF', 1))
        '''

    def get_tag(self):    #获取所有标签
        tag = self.db.select('typecho_metas', 'mid', 'name', type='"category"')
        return tag
    
    
    def recursion_category(self, category_tuple, categorys_tuple, is_print, deep):    #递归输出分类，deep控制缩进
        mid = category_tuple[0]
        name = category_tuple[1]
        
        for i, i_tuple in enumerate(categorys_tuple):    #获取当前所选元组在大元组中的位置
            if category_tuple == i_tuple:
                num = i
                break
        
        if not is_print[num]:    #输出
            print('%d\t%s%s'%(mid, ' '*deep, name))
            is_print[num] = True
            for category_tuple in categorys_tuple:    #递归
                if category_tuple[2] == mid:
                    self.recursion_category(category_tuple, categorys_tuple, is_print, deep+2)


    def get_category_tree(self, categorys_tuple):    #根据分类的从属关系形成树形层级结构，不同等级之间缩进为两个空格
        is_print = [False] * len(categorys_tuple)
        for category_tuple in categorys_tuple:
            if category_tuple[2] == 0 or category_tuple[2] == '0' :
                self.recursion_category(category_tuple, categorys_tuple, is_print, 0)
        
    
    def get_catalogue(self, mid):    #显示分类或标签下的文章目录
        
        res = self.db.select('typecho_relationships', 'cid', mid=mid)
        catalogue = []
        for ress in res:
            passage = self.db.select('typecho_contents', 'cid', 'title', cid=ress[0])
            if passage:
                catalogue.append(passage[0])
        return catalogue


    def get_passage(self, cid):    #获取文章文本
        res = self.db.select('typecho_contents', 'title', 'text', cid=cid)
        name = res[0][0]
        text = res[0][1].replace(r'<!--markdown-->','')
        file_path = os.path.join(self.localDir, name+'.md')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)
        return (file_path, text)
    
    
    def make_category(self):   #创建新分类
        name = input('请输入分类名称：')
        res = self.db.select('typecho_metas', 'mid', name='"%s"'%name)
        if not res:    #分类名不存在,避免重复
            slug = input('请输入分类缩略名：')
            res = self.db.select('typecho_metas', 'mid', slug='"%s"'%slug)
            if not res:    #缩略名不存在,避免重复
                description = input('请输入分类描述（可留空）：')
                parent = int(input('请输入分类的父级分类（无父级分类请输入0）：'))
                if parent != 0:
                    res = self.db.select('typecho_metas', 'mid', mid=parent)
                    if not res:    #父级分类要存在,不存在则退出
                        print('mid为%d的父级分类不存在哦'%parent)
                        return None
                        
                #mid = self.db.insert('typecho_metas', name=name, slug=slug, type='catetory', description=description, parent=parent)
                #通过数据库操作，一直无法插入分类，因为order无法通过数据库的select、insert的方式写入，数据库会报语句错误，好奇怪。
                #但是没有order就不会显示这个分类。所以改用post的方式通过web端创建新的分类
                #order在官方的解释是排版的顺序
                post = P.POST(self.url, self.token1, self.ip, self.user, self.password, self.database)
                post.login()
                post.make_category(name, slug, parent, description)
                mid = self.db.select('typecho_metas', 'mid', name='"%s"'%name)
                
                if mid:
                    print('已选择刚创建的新目录')
                    return mid
                else:
                    print('创建目录失败')
            else:
                print('缩略名已存在')
        else:
            print('分类名已存在')
            
    
    def find_cid_by_catalogue(self):    #从分类的目录页开始选择，最终找到文章的cid 
        
        print('独立页面的文章有：')
        res = self.db.select('typecho_contents', 'cid', type='"page"')
        for ress in res:
            passages = self.db.select('typecho_contents', 'cid', 'title', cid=ress[0])
            for passage in passages:
                if passage:
                    print('%s\t%s'%(passage[0], passage[1]))
            
        cid = input('如果已知文章cid，可直接输入，如不知道，直接回车，通过分类来寻找文章cid：')
        if not cid == '':
            return int(cid)
        else:
            #选择文章所属分类
            categorys = self.get_category()
            print('\n共%d个分类，输入-1可退出程序' % len(categorys))
            print('mid\t分类')
            self.get_category_tree(categorys)
            mid = int(input('请选择文章所属分类:'))
            if mid == -1:
                return None
            
            #在分类界面找到文章
            passages = self.get_catalogue(mid)
            #print(passages,222222222)
            print('\n共%d篇文章，输入-1可退出程序' % len(passages))
            #print(passages,222222222)
            for passage in passages:    #获取文章cid
                cid = passage[0]
                title = passage[1]
                print('%d\t%s'%(cid, title))
            cid = int(input('请选择文章：'))
            if cid == -1:
                return None
            else:
                return cid
    
    
    def upload_passage(self, insert_or_update, text, cid='', title='', mid_tuple='', field_list=''):
        
        '''
        insert_or_update为'insert'表示上传全新文章（数据库中不存在）',为'update'表示上传修改文章（数据库中存在）
        insert时操作多，而update只包括上传文章和非本站图片并更新修改时间，不包括分类、自定义字段等
        insert使用text, title, mid_tuple, field_list
        update只使用text, cid
        '''
        #要想在在md中将图片的本地路径改为网络路径，先要上传图片，获取url，在文本中修改，上传文本后获取cid后，还要修改刚刚上传的图片的parent
        
        pic_list = pic.find_pics(text, self.url, self.localDir)    #获取所有图片（除down_own_pic为False的本站图片外的所有图片）
        pic.upload_pics(pic_list, self.url, self.token1, self.ip, self.user, self.password, self.database)    #上传所有图片
        
        for pic_dict in pic_list:    #将本地图片地址改为在博客上的网址
            text = text.replace(pic_dict['tag'], pic_dict['upload_path'])
            if text.find(pic_dict['tag'])  == -1:
                print('####替换%s为%s####'%(pic_dict['tag'], pic_dict['upload_path']))
        text = text.replace('"',r'\"')

        if insert_or_update == 'insert':
            ticks = int(time.time())
            passage_cid = self.db.insert('typecho_contents', title=title, created=ticks, modified=ticks, text=text, authorId=self.db.user_uid, type='post')    #文章入库
        elif insert_or_update == 'update':
            self.db.update('typecho_contents', 'text', '"%s"'%text, cid=cid)
            ticks = int(time.time())
            self.db.update('typecho_contents', 'modified', ticks, cid=cid)
            
        if insert_or_update == 'insert':
            #print(1111111)
            #print(pic_list)
            for pic_dict in pic_list:    #修改图片的parent为passage_cid，原先为0
                self.db.update('typecho_contents', 'parent', passage_cid, cid=pic_dict['cid'])
            
            #print(mid_tuple,222222)
            for mid in mid_tuple:   #给文章添加标签、分类
                self.db.insert('typecho_relationships', cid=passage_cid, mid=mid)
    
            for field in field_list:    #自定义字段
                name = field[0]
                type_ = field[1]
                type_value = field[2]
                
                if type_ == 'str':
                    if name == 'thumbnail':    #针对我自己使用的typecho插件，设置文章封面，把本地图片上传
                        if re.search(r'^https?://', type_value):    #如果是网络图片，则先下载到本地
                            dir_path = os.path.join(self.localDir, 'pic')
                            if not os.path.exists(dir_path):
                                os.makedirs(dir_path)
                            pic_path = pic.down_pic(type_value, dir_path)
                            type_value = pic_path   #将下载图片的本地路径重新赋值给type_value(之前存储的是网络地址)
                        pic_dict = pic.upload_pic(type_value, 'cover.png', self.url, self.token1, self.ip, self.user, self.password, self.database)
                        self.db.update('typecho_contents', 'parent', passage_cid, cid=pic_dict['cid'])
                        self.db.insert('typecho_fields', cid=passage_cid, name=name, type=type_, str_value=pic_dict['upload_path'])
                    else:
                        self.db.insert('typecho_fields', cid=passage_cid, name=name, type=type_, str_value=type_value)
                elif type_ == 'int':
                    self.db.insert('typecho_fields', cid=passage_cid, name=name, type=type_, int_value=type_value)
                elif type_ == 'float':
                    self.db.insert('typecho_fields', cid=passage_cid, name=name, type=type_, float_value=type_value)
        
    

    def cmd(self):
        
        #选择操作
        actions = {
                '1': '下载文章（不下载图片，适用于修改文章后再次上传）',
                '2': '下载文章（下载全部图片，适用于本地的备份）',
                '3': '下载文章（图片以base64形式2写入md文件，便于分享）',#TODO
                '4': '上传全新文章（数据库中不存在）',
                '5': '上传修改文章（数据库中存在）',
                '6': '删除文章',
                '7': '移动文章（所属分类）',
                '8': '创建分类',
                '9': '删除目录',#TODO
                }
        for num, action in actions.items():
            print(num, action)
        num = int(input('选择'))
        
        #下载文章（不下载图片）
        if num == 1:
            cid = self.find_cid_by_catalogue()
            if cid:
                self.get_passage(cid)
        
        
        #下载文章（下载图片）。图片下载至所选的目录文件夹下的pic文件夹，文档中的图片网址链接会改为本地图片链接       
        elif num == 2:
            cid = self.find_cid_by_catalogue()
            if cid:
                text_tuple = self.get_passage(cid)
                file_path = text_tuple[0]
                text = text_tuple[1]
                pic_list = pic.find_pics(text, self.url, self.localDir, True)
                for pic_dict in pic_list:    #将网络图片地址改为本地图片地址
                    try:
                        text = text.replace(pic_dict['tag'], pic_dict['local_path'])    #有个问题，如果正文中出现了pic_dict['tag']的值怎么办？TODO
                        if text.find(pic_dict['tag'])  == -1:
                            print('####替换%s为%s####'%(pic_dict['tag'], pic_dict['local_path']))
                    except Exception as e:
                        print('替换图片地址失败，错误%s'%e)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text)
              
                
        elif num == 3:
            pass
        
        
        #上传全新文章（数据库中不存在）
        elif num == 4:
            file_path = input('请输入文件路径(直接回车则列出本地缓存文件夹下所有md文件以供选择)：')
            if file_path == '':
                files = os.listdir(self.localDir)
                files_dict = {}
                i = 1
                for file in files:
                    if re.search(r'\.md$', file):
                        files_dict['%d'%i] = file
                        i += 1
                for num, file in files_dict.items():
                    print('%s\t%s'%(num, file))
                num = input('请选择文章：')
                file = files_dict['%s'%num]
                file_path = os.path.join(self.localDir, file)
                
            elif not re.search(r'\.md$', file_path):
                print('选择文件不是markdown文件')
                return None

            text = r'<!--markdown-->'
            with open(file_path,'r',encoding='utf-8')as f:
                text += str(f.read())
                
            title = input('请输入文章标题（直接回车则以文件名作为标题）：')
            if title == '':
                title = str(os.path.split(file_path)[1])[:-3]    #去掉.md的后缀
            
            categorys = self.get_category()
            print('\n共以下%d个分类，输入0可创建新分类：' % len(categorys))
            self.get_category_tree(categorys)
            mid_str = input('请选择文章所属分类，同时属于多个分类时以英文逗号分割:')
            if mid_str == '':
                mid = '0'    #分类显示为无，但不是在默认分类
            elif mid_str == '0':
                mid = self.make_category()    #创建新分类并选择该新分类
            mid = eval('(%s,)'%mid_str)    #元组

            with open('typecho.conf') as f:    #自定义字段
                file = f.read()
            conf_list = json.loads(file)
            field_list = conf_list[1]
            field_list_param = []
            for field_dict in field_list:
                print(field_dict['detail'])
                value = input()
                if value:
                    field_tuple = (field_dict['name'], field_dict['type'], value)
                    field_list_param.append(field_tuple)
            
            self.upload_passage('insert', text, title=title, mid_tuple=mid, field_list=field_list_param)
        
        
        #上传修改文章（数据库中存在）
        elif num == 5:
            print('请按提示依次选择此文章所属的分类和标题，以获取文章cid：')
            cid = self.find_cid_by_catalogue()
            if cid:
                file_path = input('请输入文件路径(直接回车则默认在本地缓存文件夹下寻找以所选文章标题为标题的md文件)：')
                
                if file_path == '':
                    title = self.db.select('typecho_contents', 'title', cid=cid)[0][0]
                    file_path = os.path.join(self.localDir, title+'.md')
                    
                if not re.search(r'\.md$', file_path):
                    print('选择文件不是markdown文件')
                    return None
                
                if not os.path.exists(file_path):
                    print('不存在%s'%file_path)
                    return None
            
                text = r'<!--markdown-->'
                with open(file_path,'r',encoding='utf-8')as f:
                    text += str(f.read())
                self.upload_passage('update', text=text, cid=cid)
        
        
        #删除文章
        elif num == 6:
            cid = self.find_cid_by_catalogue()
            if cid:
                self.db.delete('typecho_contents', cid=cid)
                self.db.delete('typecho_contents', parent=cid)
                self.db.delete('typecho_fields', cid=cid)
                self.db.delete('typecho_relationships', cid=cid)
        
        
        #'移动文章（所属分类）'
        elif num == 7:
            cid = self.find_cid_by_catalogue()
            
            if cid:
                categorys = self.get_category()
                print('\n共%d个分类，输入-1可退出程序' % len(categorys))
                print('mid\t分类')
                self.get_category_tree(categorys)
                mid_str = input('移动文章至（同时属于多个分类时以英文逗号分割）：')
                
                self.db.delete('typecho_relationships', cid=cid)

                if mid_str == '':
                    mid = '0'    #分类显示为无，但不是在默认分类
                elif mid_str == '0':
                    mid = self.make_category()    #创建新分类并选择该新分类
                mid_tuple = eval('(%s,)'%mid_str)    #元组
                for mid in mid_tuple:
                    self.db.insert('typecho_relationships', mid=mid, cid=cid)


        elif num == 8:
            categorys_tuple = self.get_category()
            self.get_category_tree(categorys_tuple)
            self.make_category()

        else:
            print('没有这样的操作哦')


if __name__ == '__main__':

    if os.path.exists('typecho.conf'):
        with open('typecho.conf') as f:
            file = f.read()
        conf_list = json.loads(file)
        user_list = conf_list[0]
        for n, user in enumerate(user_list):
            print(n+1, ': ',user['url'])
        num = input('请选择博客：')
        if int(num) > len(user_list) or int(num) == 0:
            print('用户不存在')
        else:
            user_dict = user_list[int(num)-1]
            typecho = Typecho(user_dict)
            typecho.cmd()
    else:
        print('请先通过blogs_settings.py配置博客信息')