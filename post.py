import copy, requests
import PyMySQL


def md5(string):
    import hashlib
    m = hashlib.md5()
    m.update(bytes(string, 'utf-8'))
    return str(m.hexdigest()).lower()


def url_encode(string):
    from urllib.parse import quote
    return quote(string, 'utf-8')


class POST():
    
    def __init__(self, url, token1, ip, user, password, database):
        self.base_url = url
        self.token1 = token1
        self.ip = ip
        self.user=user 
        self.password = password
        self.database = database
        self.session = requests.Session()
        self.session_login = requests.Session()
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'
        self.proxies = {'http':'127.0.0.1:8080','https': '127.0.0.1:8080'}    #burpsuite抓包


    def login(self):
        print('####登录后台中####')
        token4 = '{}/admin/login.php?referer={}%2Fadmin%2F'.format(self.base_url, url_encode(self.base_url))
        token = md5(self.token1 + '&' + token4)
        url = self.base_url + '/index.php/action/login?_=%s' % token
        data = {
            'name': 'admin',
            'password': 'DdhjX520',
            'referer': '{}%2Fadmin%2F'.format(url_encode(self.base_url))
            }
        headers = {
            'User-Agent': self.user_agent,
            'Referer': token4,
            }
        self.session.post(url, data, headers=headers)
        self.session_login = copy.deepcopy(self.session)
        print('Cookies:', self.session.cookies.get_dict())

        '''
        啊啊啊，之前把获取authCode的语句放在了init里面，但是实际上每次登录，
        authCode都会改变，所以每次使用的都是上一次的authCode，因而token永远都是旧的，
        一直302跳转至write-page界面，好几个小时才从数据库中发现这个错误
        '''
        db = PyMySQL.DB(self.ip, self.user, self.password, self.database)    
        self.token2 = str(db.user_authCode)
        self.token3 = str(db.user_uid)


    def upload_pic(self, pic_path, name):    
        '''
        name要带后缀，否则上传失败
        '''
        name = url_encode(name)    #中文名称的图片，typecho会url转码
        print('####正在上传%s####'%pic_path)
        
        token4 = r'{}/admin/write-post.php'.format(self.base_url)
        token = self.token1 + '&' + self.token2 + '&' + self.token3 + '&' + token4
        token = md5(token)

        url = self.base_url + '/index.php/action/upload?_=%s' % token
        data = {'name': name}
        files = {'file': (name, open(pic_path, 'rb'))}
        headers = {
            'User-Agent': self.user_agent,
            'Referer': token4,
            }
        #proxies = {'http':'127.0.0.1:8080','https': '127.0.0.1:8080'} 
        r = self.session.post(url, data, files=files, headers=headers)#, proxies=proxies)
        #print(r.text)
        self.session = copy.deepcopy(self.session_login)
        return r
    
    
    def make_category(self, name, slug, parent, description):
        '''
        该函数并没有判断是否分类名和缩略名是否已存在的机制，也没有检测是否插入成功的机制
        使用前请加入判重机制，以及使用后判断是否插入成功的机制
        '''
        if parent == 0:
            token4 = r'{}/admin/category.php'.format(self.base_url)
        else:
            token4 = r'{}/admin/category.php?parent={}'.format(self.base_url, parent)
        token = self.token1 + '&' + self.token2 + '&' + self.token3 + '&' + token4
        token = md5(token)

        url = self.base_url + '/index.php/action/metas-category-edit?_=%s' % token
        data = {
                'name': name,
                'slug': slug,
                'parent': parent,
                'description': description,
                'do': 'insert',
                'mid': ''    #开始没加do和mid,不行，只加do也不行，必须都加
                }
        headers = {
            'User-Agent': self.user_agent,
            'Referer': token4,
            }
        #proxies = {'http':'127.0.0.1:8080','https': '127.0.0.1:8080'} 
        self.session.post(url, data, headers=headers)
        self.session = copy.deepcopy(self.session_login)
    

if __name__ == '__main__':
    url = 'http://localhost/blog2'
    token1 = 'IEqbi2CiS5UrOlKtFRMzTQ)S2)G33EFd'
    ip = '127.0.0.1'
    user = 'root'
    password = 'root'
    database = 'blog2'
    
    post = POST(url, token1, ip, user, password, database)
    post.login()
    r = post.make_category('1扫宿f舍63','34dfd65', 9, '3323')
    print(r.text)