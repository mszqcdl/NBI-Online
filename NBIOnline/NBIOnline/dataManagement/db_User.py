import pymongo
import time
import datetime
from ..imageProcess.NBIGenerator import getRandom
import random


# '''
# 用户信息表: UserInfo
# | 字段名          | 类型   | 含义                                                                     |
# | -------------- | ------- | -------------------------------------------------------------------------|
# | UID            | String  | email地址                                                                |
# | pwd            | String  | md5加密后的密码                                                           |
# | registerTime   | Time    | 注册时间                                                                  |
# | name           | String  | 用户昵称（初始为随机）                                                     |
# | rank           | Integer | 用户等级（1=普通；2=超级）                                                  |
# | expiresTime    | Time    | 高级用户过期时间戳                                                        |
# | workPlace      | String  | 用户工作单位（初始为空）                                                   |
# | department     | String  | 用户工作部门（初始为空）                                                   |
# | competent      | String  | 用户职称（初始为空）                                                       |
# | inviteCode     | String  | 邀请码                                                                  |
# | isSend         | Boolean | 是否已经赠送过邀请码？true表示已经赠送（每人赠送一次，可多次接受）
# | SUM_generate   | Integer | 记录用户生成的总NBI张数                                                    |
# | TIMES_generate | Integer | 可生成NBI图片数，-1表示不限量                                               |
# '''

# '''
# 普通用户与高级用户的区别：
# 普通用户的下载图片是压缩后的图片，无法下载高清晰度原图；
# 普通用户每天有10次的生成次数限制;

# 普通用户与高级用户的判别：
# rank==2且当前时间没有超过它的高级用户过期时间戳
# '''
from ..userManagement.md5 import transToMD5


class User:
    def __init__(self, uid, pwd, rank=2, name=None, workPlace=None,
                 department=None, competent=None):
        self.uid = uid
        self.pwd = pwd
        self.registerTime = time.time()
        self.rank = rank
        if name is None:
            self.name = "User" + getRandom() + str(int(time.time()) % 10000)
        # 刚刚注册给予3天高级用户身份
        self.expiresTime = time.mktime(
            time.strptime((datetime.datetime.now() + datetime.timedelta(days=3)).strftime("%Y-%m-%d 00:00:00"),
                          '%Y-%m-%d %H:%M:%S'))
        self.workPlace = workPlace
        self.department = department
        self.competent = competent
        self.inviteCode = getInviteCode()
        self.isSend = False
        self.SUM_generate = 0
        self.TIMES_generate = -1

    def getDict(self):
        ret = dict()
        ret['UID'] = self.uid
        ret['pwd'] = self.pwd
        ret['registerTime'] = self.registerTime
        ret['name'] = self.name
        ret['rank'] = self.rank
        ret['expiresTime'] = self.expiresTime
        ret['workPlace'] = self.workPlace
        ret['department'] = self.department
        ret['competent'] = self.competent
        ret['inviteCode'] = self.inviteCode
        ret['isSend'] = self.isSend
        ret['SUM_generate'] = self.SUM_generate
        ret['TIMES_generate'] = self.TIMES_generate
        return ret

    def saveNewUser(self):
        conn = pymongo.MongoClient(
            'mongodb://{}:{}@{}:{}/?authSource={}'.format("root", "buptweb007", "49.232.229.126", "27017", "admin"))
        table = conn.nbi.UserInfo
        ret = table.insert_one(self.getDict())
        conn.close()
        return ret


def getInviteCode():
    #   digits="0123456789"
    ascii_letters = "0123456789abcdefghigklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    str_list = [random.choice(ascii_letters) for i in range(35)]
    random_str = '~' + ''.join(str_list)
    return random_str


def getUnameByUID(uid):
    conn = pymongo.MongoClient(
        'mongodb://{}:{}@{}:{}/?authSource={}'.format("root", "buptweb007", "49.232.229.126", "27017", "admin"))
    table = conn.nbi.UserInfo
    ret = table.find_one({'UID': uid})
    conn.close()
    if ret is not None:
        return ret.get("name")
    return "未登录"


def getUserInfoByUID(uid):
    conn = pymongo.MongoClient(
        'mongodb://{}:{}@{}:{}/?authSource={}'.format("root", "buptweb007", "49.232.229.126", "27017", "admin"))
    table = conn.nbi.UserInfo
    ret = table.find_one({'UID': uid})
    conn.close()
    if ret is not None:
        return ret
    return None


def updateUname(uid, uname):
    conn = pymongo.MongoClient(
        'mongodb://{}:{}@{}:{}/?authSource={}'.format("root", "buptweb007", "49.232.229.126", "27017", "admin"))
    table = conn.nbi.UserInfo
    newValue = {"$set": {"name": uname}}
    result = table.update_one({"UID": uid}, newValue)
    conn.close()
    return result


def updateAddInfo(uid, workPlace, department, competent):
    conn = pymongo.MongoClient(
        'mongodb://{}:{}@{}:{}/?authSource={}'.format("root", "buptweb007", "49.232.229.126", "27017", "admin"))
    table = conn.nbi.UserInfo
    newValue = {"$set": {"workPlace": workPlace, "department": department, "competent": competent}}
    result = table.update_one({"UID": uid}, newValue)
    conn.close()
    return result


# 检查是否有次数，有则减一并返回true，无则返回false
def checkGenerateTimes(uid):
    conn = pymongo.MongoClient(
        'mongodb://{}:{}@{}:{}/?authSource={}'.format("root", "buptweb007", "49.232.229.126", "27017", "admin"))
    table = conn.nbi.UserInfo
    times = table.find_one({"UID": uid})['TIMES_generate']
    if times > 0:
        newValue = {"$set": {"TIMES_generate": times - 1}}
        table.update_one({"UID": uid}, newValue)
        conn.close()
        return True
    else:
        conn.close()
        return False


# 生成总条数加一
def addSumGenerate(uid):
    conn = pymongo.MongoClient(
        'mongodb://{}:{}@{}:{}/?authSource={}'.format("root", "buptweb007", "49.232.229.126", "27017", "admin"))
    table = conn.nbi.UserInfo
    oldTimes = table.find_one({"UID": uid})['SUM_generate']
    newValue = {"$set": {"SUM_generate": oldTimes + 1}}
    table.update_one({"UID": uid}, newValue)
    conn.close()


# 根据邀请码查询用户信息，满足要求则给予奖励并返回true,失败返回false
def inviteCodeReward(uid, inviteCode):
    # 检查用户是否为刚注册第一天内
    conn = pymongo.MongoClient(
        'mongodb://{}:{}@{}:{}/?authSource={}'.format("root", "buptweb007", "49.232.229.126", "27017", "admin"))
    table = conn.nbi.UserInfo
    isSend = table.find_one({"UID": uid})['isSend']
    if isSend:
        return -4  # 表示已经送过了
    registerTime = table.find_one({"UID": uid})['registerTime']
    oneDayLater = registerTime + 24*60*60
    if time.time() >= oneDayLater:
        return -1  # 表示过时了
    targetUID = table.find({"inviteCode": inviteCode})
    if targetUID.count() != 1:
        return -2  # 表示找不到那个人，可能输错了
    targetUser = targetUID[0]
    # 排除自己邀请自己的情况
    if targetUser['UID'] == uid:
        return -3

    newValue = {"$set": {"isSend": True}}
    table.update_one({"UID": uid}, newValue)

    addSuperDay(targetUser, 30)
    conn.close()
    return 1


def addSuperDay(user, num):
    conn = pymongo.MongoClient(
        'mongodb://{}:{}@{}:{}/?authSource={}'.format("root", "buptweb007", "49.232.229.126", "27017", "admin"))
    table = conn.nbi.UserInfo
    # 先看是否是超级用户，如果是就直接加上时间，不是则在当前的基础上加上时间
    if user['expiresTime'] >= time.time():
        # 没过期
        newExpiresTime = user['expiresTime'] + num * 24 * 60 * 60
    else:
        newExpiresTime = time.time() + num * 24 * 60 * 60
    newValue = {"$set": {"expiresTime": newExpiresTime}}
    table.update_one({"UID": user["UID"]}, newValue)
    conn.close()


# 输入旧密码，更新为新密码，旧密码不对则返回false,对的则返回true,并且更新
def changePwd(uid, oldPwd, newPwd):
    conn = pymongo.MongoClient(
        'mongodb://{}:{}@{}:{}/?authSource={}'.format("root", "buptweb007", "49.232.229.126", "27017", "admin"))
    table = conn.nbi.UserInfo
    oldPwdInDatabase = table.find_one({"UID": uid})['pwd']
    if not transToMD5(oldPwd) == oldPwdInDatabase:
        return False
    newValue = {"$set": {"pwd": transToMD5(newPwd)}}
    table.update_one({"UID": uid}, newValue)
    conn.close()
    return True

