利用本工具，可以将 harbor 的 bucket 挂载到本地目录
# 运行参数说明与示例
    ./harbor_fuse.py [存储桶名称] [mount挂载点] [access_key] [secret_key]
    ./harbor_fuse.py testmount /mnt/ 337aa4943e9011e9867bc8000a00c8d3 259b5030d4eb1989cf46a011027791a48f130c3b

# Requirment:
    pip3 install fusepy
    
#相关研发资料
    fusepy官方github地址：
    https://github.com/fusepy/fusepy
    官方研发的示例：
    https://github.com/fusepy/fusepy/tree/master/examples
