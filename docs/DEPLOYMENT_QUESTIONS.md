# 部署前需要确认的问题 / Pre-deployment questions for Richard's team

Sent 2026-07-10. Answers drive the deployment shape (hosting, access, 017 scope, playbook).
The provisional technical plan these answers finalize lives in the session plan and the
SYSTEM_MAP housekeeping note (VM in Singapore/Tokyo for API egress, Caddy TLS + auth,
feature 017-deployment-readiness, Chinese playbook served at /playbook).

## 一、团队与使用方式 / Team & usage

1. 大概有几位同事会使用这个工具？他们的角色是什么（设计师、市场、运营）？
   How many people will use it, and in what roles (designer, marketing, ops)?
2. 最终"这张图行不行"由谁来判断？是一个人把关，还是每个人自己判断？
   Who makes the final taste call on a design: one gatekeeper, or each user for themselves?
3. 测试期间预计每周生成多少张设计稿？（费用参考：每张图约 $0.08，分层导出每次约 $0.5）
   Expected weekly volume during testing? (Cost: about $0.08 per image, about $0.5 per
   layered export.)
4. 工具目前一次只能处理一个生成任务（排队使用）。团队轮流用可以接受吗，还是需要多人同时出图？
   The tool processes one generation at a time. Is taking turns acceptable, or do you need
   simultaneous runs?
5. 团队里有没有偏技术的同事，可以作为我们对接的管理员联系人？
   Is there a technically inclined person who can be our admin contact?

## 二、网络环境 / Network

6. 办公室网络访问境外网站（比如部署在新加坡或东京的网页）是否稳定？公司有没有现成的 VPN 或代理？
   Can the office reliably reach foreign-hosted sites (Singapore/Tokyo)? Any existing
   corporate VPN or proxy?
7. 公司对"品牌素材（logo、VI 手册 PDF）上传到境外服务器"有没有合规或保密方面的限制？
   Any policy concerns about brand assets (logos, VI PDFs) living on a foreign-hosted server?

## 三、品牌与内容 / Brands & content

8. 先用哪些品牌测试？每个品牌是否都有 VI 手册 PDF 和 logo 源文件？（工具需要这两样来录入新品牌）
   Which brands first? Do you have the VI PDF + logo file for each (required for onboarding)?
9. 新品牌录入（一次性向导，约 10 分钟）希望由你们自己操作，还是我们代办？
   Should your team run the one-time brand onboarding wizard themselves, or should we do it?
10. 最需要的产出类型是什么（活动手举牌、社交媒体海报、门店物料）？主要用于印刷还是线上？
    Which asset types matter most (event signs, social posts, in-store)? Print or digital?
11. 分层导出（每个元素一层的 zip 包）是每张图都需要，还是选中的图才导出？
    Is the layered export needed for every design, or only selected ones?
12. 品牌字体你们是否持有授权字体文件？（近期出图的文字由 AI 绘制，后续如要精确字体需要授权文件）
    Do you hold licensed font files for the brands? (Current drafts use AI-painted type;
    exact licensed type later needs the files.)

## 四、费用与账号 / Infrastructure & billing

13. 服务器希望架在你们公司的云账号上（阿里云/腾讯云国际版等），还是我们这边托管、你们直接用网址访问？
    Host on your company cloud account, or we host and you just use a URL?
14. 服务器费用（约每月 $20-40）和 API 生成费用由哪边承担？测试期有没有预算上限？
    Who covers hosting (about $20-40/mo) and per-run API costs? Any testing budget ceiling?
15. 登录方式：整个团队共用一个密码可以吗，还是需要每人单独账号？
    Login: is one shared team password fine, or do you need individual accounts?

## 五、反馈与时间 / Feedback & timeline

16. 测试反馈走什么渠道（微信群、共享文档、每周例会）？谁是对接人？
    Feedback channel (WeChat group, shared doc, weekly call)? Who is the point of contact?
17. 中文使用手册够用吗，还是界面本身也需要中文化？
    Is a Chinese playbook sufficient, or does the interface itself need to be in Chinese?
18. 希望什么时候开始测试？
    When do you want to start testing?
