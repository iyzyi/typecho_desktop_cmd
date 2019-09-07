import pymysql

class DB():
    
    def where_str(self, **where_kwargs):
        where = ''
        for w in where_kwargs:
            where += str(w) + '=' + str(where_kwargs[w]) + ' and '
        where = where[:-5]
        return where

    def __init__(self, ip, user, password, database, print_sql=True):
        self.ip = ip
        self.user = user
        self.password = password
        self.database = database
        self.print_sql = print_sql

        self.db = pymysql.connect(ip, user, password, database)
        self.cursor = self.db.cursor()

        user_info = self.select('typecho_users', 'uid', 'authCode')
        self.user_uid = user_info[0][0]
        self.user_authCode = user_info[0][1]


    def select(self, table, *column_args, **where_kwargs):
        columns = ''
        for column in column_args:
            columns += column + ','
        columns = columns[:-1]

        where = self.where_str(**where_kwargs)

        if len(where) > 0 :
            sql = "SELECT {} FROM {} WHERE {};".format(columns, table, where)
        else:
            sql = "SELECT {} FROM {};".format(columns, table)
        if self.print_sql:
            print(sql)
        self.cursor.execute(sql)
        data = self.cursor.fetchall()
        return data
    

    def delete(self, table, **where_kwargs):
        where = self.where_str(**where_kwargs)

        sql = "DELETE FROM {} WHERE {};".format(table, where)
        if self.print_sql:
            print(sql)
        self.cursor.execute(sql)
        self.db.commit()

 
    def insert(self, table, **column_kwargs):

        if table == 'typecho_contents':
            '''
            cid|title|slug|created|modified|text|order|authorId|template|type|status|password|commentsNum|allowComment|allowPing|allowFeed|parent|views|
            cid 序号，文字、独立页面、图片共用。入库时自动给出cid
            title 文章标题(图片名称)
            slug 网址的缩略名，文章的slug为cid，图片的slug为图片名称（冲突时加-1区分）(但是为了方便，这里的slug从图片名称改为图片cid)，独立页面如“关于”的为start-page
            created 创建的时间，unix时间戳
            modified 修改的时间，也是时间戳
            text 正文（图片的为序列化信息）
            order  顺序，文章的order为0，上传的图片附件按上传的时间依次从1往后排（即使只是上传了而没有插入文章中），并不是在文章中的顺序哦。我就不写这个需求了，因为order保持默认的0时，并没有后果
            authorId 作者id，从typecho_users表的uid列中获取
            template 默认值NULL
            type 文章为post，独立页面为page，图片为attachment
            status 默认publish
            password 默认值NULL
            commentsNum 评论数,发送新文章时自然是0
            allowComment 默认值0,要改设为1
            allowPing 默认值0,要改设为1
            allowFeed 默认值0,要改设为1
            parent 文章、独立页面无父亲为0，图片为所在文章的cid
            views 默认值为0，但文章似乎打开过就变成1，但图片还是不变。没搞懂，先默认值吧
            总结一下，需要填写的量有title, slug, created, modified, text, order, authorId, type, allowComment, allowPing, allowFeed, parent，
            其中allowComment, allowPing, allowFeed恒为1，parent不是此环节填写的（update环节的时候更新）
            '''
            p = column_kwargs
            
            sql_print = 'INSERT INTO {}(title, created, modified, text, authorId, type, allowComment, allowPing, allowFeed) VALUES ("{}",{},{},"{}",{},"{}","{}","{}","{}");'.format(table,
                    p['title'], p['created'], p['modified'], '"####文本内容省略####"', p['authorId'], p['type'], 1, 1, 1)
            if self.print_sql:
                print(sql_print)
            
            sql = 'INSERT INTO {}(title, created, modified, text, authorId, type, allowComment, allowPing, allowFeed) VALUES ("{}",{},{},"{}",{},"{}","{}","{}","{}");'.format(table,
                    p['title'], p['created'], p['modified'], p['text'], p['authorId'], p['type'], 1, 1, 1)
            
            self.cursor.execute(sql)
            self.db.commit()
            if p['type'] == 'post':
                res = self.select('typecho_contents', 'cid', title='"%s"'%p['title'], created=p['created'])
                #根据title和创建时间找到刚刚发布的新文章。重复发送时可能会有bug
                cid = res[0][0]
                self.update('typecho_contents', 'slug', cid, title='"%s"'%p['title'], created=p['created'])
                #cid是入库时自动给出的，开始我们不知道slug，所以入库时我们不给出slug的值，先入库，再根据标题和创建时间找到刚才入库的文章的cid和type，然后修改slug
                return cid

        if table == 'typecho_fields':    #自定义字段的数据表
            '''
            cid 所属文章的id
            name 自定义的字段
            type 字符、整数、小数
            str_value,int_value,float_value 不用解释吧
            '''
            p = column_kwargs
            type_value = "%s_value" % p['type']
            if p['type'] == 'str':
                sql = 'INSERT INTO {}(cid, name, type, str_value) VALUES({},"{}","{}","{}");'.format('typecho_fields', p['cid'], p['name'],p['type'],p[type_value])
            elif p['type'] == 'int':
                sql = 'INSERT INTO {}(cid, name, type, int_value) VALUES({},"{}","{}",{});'.format('typecho_fields', p['cid'], p['name'],p['type'],p[type_value])
            elif p['type'] == 'float':
                sql = 'INSERT INTO {}(cid, name, type, float_value) VALUES({},"{}","{}",{});'.format('typecho_fields', p['cid'], p['name'],p['type'],p[type_value])
            if self.print_sql:
                print(sql)
            self.cursor.execute(sql)
            self.db.commit()

        if table == 'typecho_relationships':    #分类、标签库
            '''
            cid 文章id
            mid 分类、标签共用
            cid一对多mid
            '''
            p = column_kwargs
            sql = 'INSERT INTO {}(cid, mid) VALUES({},{})'.format(table, p['cid'], p['mid'])
            if self.print_sql:
                print(sql)
            self.cursor.execute(sql)
            self.db.commit()
            
        if table == 'typecho_metas':
            '''
            mid 分类、标签id
            name 名称
            slug 缩略名
            type category是分类,tag是标签
            description 描述
            count 文章数
            order 页面内的第几个元素
            parent 父级
                关于order，比如：
                111
                222
                  333
                  444
                555
                则555的order为3，444的order为4
            '''
            p = column_kwargs
            if p['description'] == '':
                sql = 'INSERT INTO {}(name, slug, type, parent) VALUES("{}","{}","{}",{})'.format(
                        'typecho_metas', p['name'], p['slug'], p['type'], p['parent'])
            else:
                sql = 'INSERT INTO {}(name, slug, type, description, parent) VALUES("{}","{}","{}","{}",{})'.format(
                        'typecho_metas', p['name'], p['slug'], p['type'], p['description'],p['parent'])
            if self.print_sql:
                print(sql)
            self.cursor.execute(sql)
            self.db.commit()
            res = self.select('typecho_metas', 'mid', name='"%s"'%p['name'], slug='"%s"'%p['slug'])
            mid = res[0][0]
            return mid
        
    
    def update(self, table, update_column, update_column_value, **where_kwargs):
        columns = ''
        for column in where_kwargs:
            columns += str(column) + '=' + str(where_kwargs[column]) + ' and '
        columns = columns[:-5]

        sql = 'UPDATE {} SET {}={} where {};'.format(table, update_column, update_column_value, columns)
        if update_column == 'text':
            sql_str = 'UPDATE {} SET {}={} where {};'.format(table, update_column, '"####文本内容省略####"', columns)
        else:
            sql_str = sql
        if self.print_sql:
            print(sql_str)
        self.cursor.execute(sql)
        self.db.commit()
        
        
if __name__ == '__main__':
    ip = 'iyzy.xyz'
    user = 'root'
    password = 'root'
    database = 'yjd'

    db = DB(ip, user, password, database)

    #print(db.user_uid)
    #print(db.user_authCode)

    #res = db.select('typecho_contents', 'cid','title')
    #print(res)

    #db.delete('typecho_contents', cid=1636)
    #db.insert('typecho_contents', title='试', created=1565382647, modified=1565382467, text='啦啦啦啦啦', authorId=1, type='post', parent=0)
    #db.update('typecho_contents', 'slug', '"88800"', cid=88889, title='"试"')