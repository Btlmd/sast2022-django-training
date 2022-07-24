# Leaderboard 9

Lambda X

> 2022-07-23

在 Linux 练习和 PyTorch 练习中，我们使用过一个前后端耦合的 [Leaderboard](http://121.5.165.232:14000/)。在接下来的前后端开发练习中，我们希望实现一个前后端分离的 Leaderboard。本次作业的目标是完成它的后端开发工作。


## Update
### 2022-07-24
- 修正了一个错误，将 `settings.py` 中的 `zh-cn` 修正为 `zh-hans`。
- 修正了一个错误，将 `views.py` 中的 `username: int` 修正为 `username: str`

## 功能简介

与我们之前使用的 PyTorch Leaderboard 一样，我们需要完成的基本功能包括

- 用户提交内容 ，后端对内容进行评定后在排行榜中按一定规则显示用户的排名
- 用户可以提交一个 Avatar，作为用户在排行榜中的标识

此外我们还希望包括

- 投票。用户可以给排行榜中的指定用户点赞。
  - 你可能会感觉奇怪，用户没有除了点数之外的任何信息，将如何完成投票？其实这没有什么关系，~~毕竟投票通常是按用户名称来投的~~ 



我们为大家提供了样例的前端实现与后端实现供大家部署后练习对接，或者在实现过程中参考（但不包括进行攻击练习

- 前端 http://front.sast2022.lmd.red/
  - 输入后端的部署地址进行对接
- 后端 http://back.sast2022.lmd.red/

（都是玩具，还请大家手下留情



## Part 0: 代码介绍与准备工作

本次练习以代码填空的形式进行，需要进行修改的部分在代码中留有 TODO 标识。可以按照文档中的提示，将 TODO 处的内容依次完成即可。当然，也可以不按文档的提示自行设计完成。

<img src="https://lambda-images.oss-cn-beijing.aliyuncs.com/images/2022-07-23_142654.png" alt="TODO" style="zoom:67%;" />

在作业仓库的 Django 项目 `LeaderBoard` 中，有一个名为 `lb` 应用，是我们作业需要进行实现的应用。

在代码填空中，我们预先写好了如下模型

```python
class User(models.Model):
    id = models.BigAutoField(primary_key=True)               # 主键
    username = models.CharField(max_length=255, unique=True) # 用户名
    votes = models.BigIntegerField(default=0)                # 投票数

class Submission(models.Model):
    id = models.BigAutoField(primary_key=True)               # 主键           
    user = models.ForeignKey(User, on_delete=models.CASCADE) # 对应 User
    avatar = models.TextField(null=True)                     # 用户头像的 Base64 表示(摆)
    time = models.FloatField(default=get_time)               # 提交时间
    score = models.IntegerField(null=False)                  # 评测成绩
    subs = models.CharField(max_length=255)                  # 评测小分
    # 评测小分可以将多个小分用空格分割作为字符串进行存储，如 [1, 1, 4] 可存为 "1 1 4"

    class Meta:
        unique_together = ["user", "time"]
```

此外，为了便于调试，我们配置了一个 CORS 中间件，见 `lb.apps.CorsMiddleware` 函数。



### 准备工作

在这一部分我们来完成一些基础性工作

- 安装 `requirements.txt` 中的依赖

- 将`LeaderBoard` 目录下的 `my.cnf.bak` 复制为 `my.cnf`，然后在其中配置自己的 MySQL 数据库。

- 迁移模型到数据库中

  ```bash
  python manage.py makemigrations lb
  python manage.py migrate
  ```

- 查看 `lb/utils.py`。该模块中有两个工具函数

  - `get_leaderboard` 

    - 这个函数会从所有的 Submission 中为每个用户选出最后一次提交记录，然后按分数排降序，分数相同的按提交时间排升序，然后返回。
    - 它已经被（不优雅地）实现好了。你可以浏览它，了解这个函数的功能和返回内容。

  - `judge` 

    - 这个函数接受一个 `content` 字符串，为用户提交的 `result.txt` （1000 条模型 inference 记录）

    - 其尚未实现。你需要根据 `lb` 目录下的 `ground_truth.txt` ，再结合用户的输入，计算用户的主分数和三个子分数。主分数的计算可以任意实现（你要真搞个随机生成也不是不行），三个子分数则是三个类别的正确率。

    - 当然你也可以考虑 c7w 对主分数的计算方式

      ```python
      import math
      
      def interpolate(x1, x2, y1, y2, x):
          if x < x1:
              return y1
          if x > x2:
              return y2
          return math.sqrt((x - x1) / (x2 - x1)) * (y2 - y1) + y1
      
      def main_score(result: list):
          """
          :param result: catagory accuracy, element value in [0, 1]
          :return: main_score
          """
          mean_result = sum(result) / 3
          return round(
              55 * interpolate(.5, .8, 0, 1, mean_result) +
              15 * interpolate(.5, .7, 0, 1, result[0]) +
              15 * interpolate(.5, .9, 0, 1, result[1]) +
              15 * interpolate(.5, .75, 0, 1, result[2])
          )
      ```

    - 如果用户的输入不合法，可以抛出适当的异常，我们将在视图函数中对异常进行捕获




## Part 1: API 接口

这部分介绍各个接口的约定输入输出。需要完成的部分用 `TODO` 标出。

在写好接口后，可以 `manage.py runserver` 然后使用 `Postman` 进行调试。

特别需要注意的是，发来的请求没有任何保证，要对请求进行检查防止后端直接 HTTP 500 。



### 排行榜

```
[GET] /leaderboard
```

该接口给出全部排行榜信息，先按照按照 `score` 降序排列，`score` 一样的，按照提交时间 `time` 升序排列。

对于用户的多次提交，无论分数高低，只返回最后一次提交。

#### 响应

```json
[
    {
        "user": "lambda_x",
        "score": 33,
        "subs": [22, 45, 32],
        "time": 1658419888,
        "avatar": "XXXXX"
    },
    {
        "user": "lambda_y",
        "score": 0,
        "subs": [1, 0, 0],
        "time": 1658419999,
        "avatar": "XXXXX"
    },
    ...
]
```

#### TODO

该接口已经实现好了。需要完成的是

- 配置 `lb/urls.py` 为该接口设置路由
- 在视图函数前添加装饰器，限制 HTTP 方法为 `GET`



### 提交历史

```
[GET] /history/<user>
```

该接口提供指定用户的提交历史，按照提交时间 `time` 升序排列

#### 请求参数

- 用户名称，从请求 URL 中获得。

#### 响应

该用户的全部历史提交信息。

```json
[
    {
        "score": 0.37,
        "subs": [1, 0, 0],
        "time": 1658419999
    },
    {
        "score": 99,
        "subs": [99, 99, 99],
        "time": 1658420008
    },
    ...
]
```

#### TODO

- 按照约定在完成视图函数 `history` 

  - 注意处理用户不存在的情形，例如不存在时返回一个 

    ```json
    {
        "code": -1
    }
    ```

    而最好不要搞成 HTTP 500

- 配置 `lb/urls.py` ，为该接口设置路由

  - 字符串的提取可以使用 `<slug:xxx>` 进行



### 提交

```
[POST] /submit
```

该接口用于接受用户提交的内容，进行评判，然后更新 Leaderboard。

#### 请求体样例

接收到的请求形如

```json
{
    "user": "lambda_x",
    "avatar": "...",
    "content": "..."
}
```

| 字段    | 说明                                         |
| ------- | -------------------------------------------- |
| user    | 用户名                                       |
| avatar  | 用 base64 编码的用户头像，可以直接视为字符串 |
| content | 用户提交的内容，一个字符串                   |

#### 响应

响应主要包括两部分

- `code` 表示请求的状态，0 为成功，其他表示失败
- `msg` 表示请求的说明文字，可用于前端给用户提示
- `data` 前端可能用到的数据

当用户提交成功的内容合法时，返回以下内容

```json
{
    "code": 0,
    "msg": "提交成功",
    "data": {
        "leaderboard": [
            ... // 与[排行榜]这一接口返回内容相同，为更新后的排行榜
        ]
    }
}
```

当请求参数不全时，返回

```json
{
    "code": 1,
    "msg": "参数不全啊"
}
```

当用户名长于 255 字符，返回

```json
{
    "code": -1,
    "msg": "用户名太长了"
}
```

当请求的 `avatar` 超过 100K 字符时，返回

```json
{
    "code": -2,
    "msg": "图像太大了",
}
```

当检测到用户提交的内容不合法时，返回

```json
{
    "code": -3,
    "msg": "提交内容非法呜呜"
}
```

#### TODO

- 补全这一视图函数，然后为它配置路由
- 视图函数实现思路参考
  - 先用 `json.loads(req.body)` 将请求的 JSON 转换为字典
  - 检查字典中的三个键是否存在，键不全返回 code 1
  - 检查用户名是否太长，不符合要求返回 code -1
  - 检查 `avatar` 字符串是否太长，不符合要求返回 code -2
  - 调用 `utils.judge` 对content 进行评判得到分数，函数运行过程中出现异常，返回 code -3
  - 检查用户是否已经存在，如果不存在则 `User.objects.create` 创建用户，否则获得用户实例
  - 调用 `Submission.objects.create`，传入参数构造用户。注意关键字参数 `user` 应当传入一个 `User` 实例而非用户的主键。
  - 返回 code 0 ，调用 `utils.get_leaderboard()` 获得 Leaderboard



### 投票

```
[POST] /vote
```

#### 请求体样例

```json
{
	"user": "lambda_x"
}
```

| 字段 | 说明                         |
| ---- | ---------------------------- |
| user | 接收投票的用户，这里的用户名 |

此时该用户的 `vote` 数加 1。

为了防止刷票，我们象征性地

- 拒绝 User-Agent 不太合理的请求
  - 可以使用 `req.headers` 查看请求的 HTTP 头

#### 响应

对于不符合要求的请求，返回

```json
{
    "code": -1
}
```

否则返回

```json
{
    "code": 0,
    "data": {
        "leaderboard": [
            ... // 与[排行榜]这一接口返回内容相同，为更新后的排行榜
        ]
    }
}
```

#### TODO

- 补全这一视图函数，然后为它配置路由

- 视图函数实现思路参考
  - 先检查 User-Agent 是否不合理，若不合理返回  -1 （已经实现）
  - 从 `req.body` 加载 JSON 为 dict
  - 再检查用户是否存在，不存在返回 -1
  - 如果用户存在，则将其投票数加一，然后保存
  - 返回 0，然后附上最新的 leaderboard



## Part2: 部署与对接

### 部署

本地测试好后，我们应该将程序部署到服务器上。可以参考课上演示的方法 / 参考文档 / 直接搜索，使用 uWSGI 或 uWSGI + Nginx 进行部署。

我们提供了一个 uWSGI 配置样例 `uwsgi.ini.bak ` 。你也可以选择其他配置，或者直接使用命令行运行 uWSGI。

提示：如果直接使用 uWSGI 部署，应使用 `http` ，如果使用 Nginx 反向代理，应使用 `socket`

### 对接

在完成了部署后，你可以试着与样例前端进行对接。

访问 http://front.sast2022.lmd.red/，输入后端的地址，然后可以试试能否使用这个前端与你的后端交互。



## 提交

在代码仓库中提出 Issue，于 Issue 中注明部署地址和代码仓库地址。

如果你没有部署的条件或者不想部署，也可以只提交代码仓库。

如果提交的部署地址不是 `59.66.131.240:XXXXX` 的形式（如自己的域名），可以在 Issue 中进行说明或者将 Issue 编号和学号发至 `liu-md20@mails.tinghua.edu.cn` ，便于我们统计大家的提交情况。
