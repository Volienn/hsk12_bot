import json
import os
import random
import asyncio
from datetime import datetime
import httpx
import pytz

# ============================================================
#  CẤU HÌNH — đọc từ biến môi trường (Railway sẽ inject)
# ============================================================
BOT_TOKEN      = os.environ["BOT_TOKEN"]
CHAT_ID        = os.environ["CHAT_ID"]
WORDS_PER_DAY  = int(os.environ.get("WORDS_PER_DAY", "3"))
# Giờ gửi theo giờ Việt Nam, cách nhau bởi dấu phẩy
SCHEDULE_TIMES = [t.strip() for t in os.environ.get("SCHEDULE_TIMES", "08:00,20:00").split(",")]
TIMEZONE       = pytz.timezone("Asia/Ho_Chi_Minh")
STATE_FILE     = "/app/data/state.json"
# ============================================================

VOCAB = [
    ("你","nǐ","bạn (ngôi thứ hai)","你好！(Nǐ hǎo!) - Xin chào!"),
    ("我","wǒ","tôi, tao","我是学生。(Wǒ shì xuéshēng.) - Tôi là học sinh."),
    ("他","tā","anh ấy, ông ấy","他很高。(Tā hěn gāo.) - Anh ấy rất cao."),
    ("她","tā","cô ấy, bà ấy","她是我的朋友。(Tā shì wǒ de péngyou.) - Cô ấy là bạn tôi."),
    ("我们","wǒmen","chúng tôi","我们去吃饭。(Wǒmen qù chīfàn.) - Chúng tôi đi ăn cơm."),
    ("你们","nǐmen","các bạn","你们好吗？(Nǐmen hǎo ma?) - Các bạn có khỏe không?"),
    ("他们","tāmen","họ (nam hoặc hỗn hợp)","他们是朋友。(Tāmen shì péngyou.) - Họ là bạn bè."),
    ("好","hǎo","tốt, tốt lắm","这很好。(Zhè hěn hǎo.) - Cái này rất tốt."),
    ("是","shì","là","我是中国人。(Wǒ shì Zhōngguórén.) - Tôi là người Trung Quốc."),
    ("不","bù","không (phủ định)","我不去。(Wǒ bù qù.) - Tôi không đi."),
    ("有","yǒu","có","我有一本书。(Wǒ yǒu yī běn shū.) - Tôi có một cuốn sách."),
    ("在","zài","ở, đang (ở nơi nào)","我在家。(Wǒ zài jiā.) - Tôi đang ở nhà."),
    ("吗","ma","(trợ từ nghi vấn)","你是学生吗？(Nǐ shì xuéshēng ma?) - Bạn có phải học sinh không?"),
    ("的","de","(trợ từ sở hữu)","我的书。(Wǒ de shū.) - Sách của tôi."),
    ("了","le","(trợ từ hoàn thành)","我吃了。(Wǒ chī le.) - Tôi đã ăn rồi."),
    ("吃","chī","ăn","我想吃饭。(Wǒ xiǎng chīfàn.) - Tôi muốn ăn cơm."),
    ("喝","hē","uống","我喝水。(Wǒ hē shuǐ.) - Tôi uống nước."),
    ("说","shuō","nói","他说中文。(Tā shuō Zhōngwén.) - Anh ấy nói tiếng Trung."),
    ("看","kàn","nhìn, xem","我看书。(Wǒ kàn shū.) - Tôi đọc sách."),
    ("听","tīng","nghe","我听音乐。(Wǒ tīng yīnyuè.) - Tôi nghe nhạc."),
    ("去","qù","đi (đến nơi nào)","我去学校。(Wǒ qù xuéxiào.) - Tôi đi học."),
    ("来","lái","đến, lại","请进来！(Qǐng jìnlái!) - Mời vào!"),
    ("回","huí","quay lại, về","我回家了。(Wǒ huí jiā le.) - Tôi về nhà rồi."),
    ("买","mǎi","mua","我买苹果。(Wǒ mǎi píngguǒ.) - Tôi mua táo."),
    ("叫","jiào","gọi là, tên là","我叫小明。(Wǒ jiào Xiǎomíng.) - Tôi tên là Tiểu Minh."),
    ("想","xiǎng","muốn, nghĩ","我想睡觉。(Wǒ xiǎng shuìjiào.) - Tôi muốn ngủ."),
    ("爱","ài","yêu, yêu thích","我爱你。(Wǒ ài nǐ.) - Tôi yêu bạn."),
    ("喜欢","xǐhuān","thích","我喜欢猫。(Wǒ xǐhuān māo.) - Tôi thích mèo."),
    ("知道","zhīdào","biết","我知道了。(Wǒ zhīdào le.) - Tôi biết rồi."),
    ("认识","rènshi","quen biết","我认识他。(Wǒ rènshi tā.) - Tôi quen anh ấy."),
    ("一","yī","một","一个苹果。(Yī gè píngguǒ.) - Một quả táo."),
    ("二","èr","hai","两个人。(Liǎng gè rén.) - Hai người."),
    ("三","sān","ba","三本书。(Sān běn shū.) - Ba cuốn sách."),
    ("四","sì","bốn","四个杯子。(Sì gè bēizi.) - Bốn cái cốc."),
    ("五","wǔ","năm","五只猫。(Wǔ zhī māo.) - Năm con mèo."),
    ("六","liù","sáu","六点钟。(Liù diǎn zhōng.) - Sáu giờ."),
    ("七","qī","bảy","七天。(Qī tiān.) - Bảy ngày."),
    ("八","bā","tám","八月。(Bā yuè.) - Tháng tám."),
    ("九","jiǔ","chín","九点。(Jiǔ diǎn.) - Chín giờ."),
    ("十","shí","mười","十个人。(Shí gè rén.) - Mười người."),
    ("百","bǎi","trăm","一百元。(Yī bǎi yuán.) - Một trăm tệ."),
    ("中国","Zhōngguó","Trung Quốc","我去中国。(Wǒ qù Zhōngguó.) - Tôi đi Trung Quốc."),
    ("北京","Běijīng","Bắc Kinh","北京很大。(Běijīng hěn dà.) - Bắc Kinh rất lớn."),
    ("学校","xuéxiào","trường học","学校在那里。(Xuéxiào zài nàlǐ.) - Trường học ở đó."),
    ("家","jiā","nhà, gia đình","我的家很小。(Wǒ de jiā hěn xiǎo.) - Nhà tôi rất nhỏ."),
    ("医院","yīyuàn","bệnh viện","医院在哪里？(Yīyuàn zài nǎlǐ?) - Bệnh viện ở đâu?"),
    ("饭店","fàndiàn","nhà hàng, khách sạn","这家饭店很好。(Zhè jiā fàndiàn hěn hǎo.) - Nhà hàng này rất tốt."),
    ("商店","shāngdiàn","cửa hàng","商店几点开？(Shāngdiàn jǐ diǎn kāi?) - Cửa hàng mở cửa lúc mấy giờ?"),
    ("书","shū","sách","这本书很好看。(Zhè běn shū hěn hǎokàn.) - Cuốn sách này rất hay."),
    ("水","shuǐ","nước","我要喝水。(Wǒ yào hē shuǐ.) - Tôi muốn uống nước."),
    ("饭","fàn","cơm, bữa ăn","吃饭了吗？(Chīfàn le ma?) - Ăn cơm chưa?"),
    ("面条","miàntiáo","mì sợi","我爱吃面条。(Wǒ ài chī miàntiáo.) - Tôi thích ăn mì."),
    ("苹果","píngguǒ","quả táo","苹果很甜。(Píngguǒ hěn tián.) - Táo rất ngọt."),
    ("茶","chá","trà","我喝茶。(Wǒ hē chá.) - Tôi uống trà."),
    ("杯子","bēizi","cái cốc","这个杯子是我的。(Zhège bēizi shì wǒ de.) - Cái cốc này là của tôi."),
    ("猫","māo","con mèo","猫很可爱。(Māo hěn kě'ài.) - Mèo rất đáng yêu."),
    ("狗","gǒu","con chó","我有一只狗。(Wǒ yǒu yī zhī gǒu.) - Tôi có một con chó."),
    ("人","rén","người","他是好人。(Tā shì hǎorén.) - Anh ấy là người tốt."),
    ("朋友","péngyou","bạn bè","他是我的朋友。(Tā shì wǒ de péngyou.) - Anh ấy là bạn tôi."),
    ("老师","lǎoshī","giáo viên","老师很好。(Lǎoshī hěn hǎo.) - Giáo viên rất tốt."),
    ("学生","xuéshēng","học sinh","我是学生。(Wǒ shì xuéshēng.) - Tôi là học sinh."),
    ("妈妈","māma","mẹ","妈妈做饭。(Māma zuò fàn.) - Mẹ nấu cơm."),
    ("爸爸","bàba","bố","爸爸工作。(Bàba gōngzuò.) - Bố đi làm."),
    ("哥哥","gēge","anh trai","哥哥很高。(Gēge hěn gāo.) - Anh trai rất cao."),
    ("姐姐","jiějie","chị gái","姐姐很漂亮。(Jiějie hěn piàoliang.) - Chị gái rất xinh."),
    ("弟弟","dìdi","em trai","弟弟八岁。(Dìdi bā suì.) - Em trai tám tuổi."),
    ("妹妹","mèimei","em gái","妹妹很可爱。(Mèimei hěn kě'ài.) - Em gái rất đáng yêu."),
    ("年","nián","năm (thời gian)","今年是哪年？(Jīnnián shì nǎ nián?) - Năm nay là năm nào?"),
    ("月","yuè","tháng, mặt trăng","这个月很忙。(Zhège yuè hěn máng.) - Tháng này rất bận."),
    ("日","rì","ngày","今天几号？(Jīntiān jǐ hào?) - Hôm nay ngày mấy?"),
    ("今天","jīntiān","hôm nay","今天天气好。(Jīntiān tiānqì hǎo.) - Hôm nay thời tiết đẹp."),
    ("明天","míngtiān","ngày mai","明天见！(Míngtiān jiàn!) - Hẹn gặp ngày mai!"),
    ("昨天","zuótiān","hôm qua","昨天我很忙。(Zuótiān wǒ hěn máng.) - Hôm qua tôi rất bận."),
    ("上","shàng","trên, lên","书在桌子上。(Shū zài zhuōzi shàng.) - Sách ở trên bàn."),
    ("下","xià","dưới, xuống","猫在椅子下。(Māo zài yǐzi xià.) - Mèo ở dưới ghế."),
    ("大","dà","to, lớn","这个房间很大。(Zhège fángjiān hěn dà.) - Phòng này rất rộng."),
    ("小","xiǎo","nhỏ","这只猫很小。(Zhè zhī māo hěn xiǎo.) - Con mèo này rất nhỏ."),
    ("多","duō","nhiều","今天人很多。(Jīntiān rén hěn duō.) - Hôm nay nhiều người."),
    ("少","shǎo","ít","水太少了。(Shuǐ tài shǎo le.) - Nước ít quá."),
    ("很","hěn","rất","这里很好。(Zhèlǐ hěn hǎo.) - Nơi này rất tốt."),
    ("太","tài","quá","今天太热了。(Jīntiān tài rè le.) - Hôm nay nóng quá."),
    ("也","yě","cũng","我也去。(Wǒ yě qù.) - Tôi cũng đi."),
    ("都","dōu","đều, tất cả","我们都是学生。(Wǒmen dōu shì xuéshēng.) - Chúng tôi đều là học sinh."),
    ("没有","méiyǒu","không có","我没有钱。(Wǒ méiyǒu qián.) - Tôi không có tiền."),
    ("什么","shénme","cái gì","你叫什么名字？(Nǐ jiào shénme míngzi?) - Bạn tên là gì?"),
    ("哪里","nǎlǐ","ở đâu","你住在哪里？(Nǐ zhù zài nǎlǐ?) - Bạn sống ở đâu?"),
    ("这","zhè","này, đây","这是我的。(Zhè shì wǒ de.) - Đây là của tôi."),
    ("那","nà","kia, đó","那是什么？(Nà shì shénme?) - Kia là gì?"),
    ("怎么","zěnme","như thế nào","怎么去？(Zěnme qù?) - Đi như thế nào?"),
    ("为什么","wèishénme","tại sao","你为什么哭？(Nǐ wèishénme kū?) - Bạn tại sao khóc?"),
    ("多少","duōshǎo","bao nhiêu","多少钱？(Duōshǎo qián?) - Bao nhiêu tiền?"),
    ("请","qǐng","xin, mời","请坐。(Qǐng zuò.) - Mời ngồi."),
    ("谢谢","xièxiè","cảm ơn","谢谢你！(Xièxiè nǐ!) - Cảm ơn bạn!"),
    ("对不起","duìbuqǐ","xin lỗi","对不起！(Duìbuqǐ!) - Xin lỗi!"),
    ("再见","zàijiàn","tạm biệt","明天再见！(Míngtiān zàijiàn!) - Hẹn gặp lại ngày mai!"),
    ("可以","kěyǐ","có thể, được phép","我可以进来吗？(Wǒ kěyǐ jìnlái ma?) - Tôi có thể vào không?"),
    ("要","yào","muốn, cần","我要一杯水。(Wǒ yào yī bēi shuǐ.) - Tôi muốn một ly nước."),
    ("会","huì","biết (kỹ năng)","我会说中文。(Wǒ huì shuō Zhōngwén.) - Tôi biết nói tiếng Trung."),
    ("能","néng","có thể (khả năng)","你能帮我吗？(Nǐ néng bāng wǒ ma?) - Bạn có thể giúp tôi không?"),
    ("工作","gōngzuò","công việc, làm việc","他工作很努力。(Tā gōngzuò hěn nǔlì.) - Anh ấy làm việc rất chăm chỉ."),
    ("学习","xuéxí","học tập","我每天学习中文。(Wǒ měitiān xuéxí Zhōngwén.) - Tôi học tiếng Trung mỗi ngày."),
    ("睡觉","shuìjiào","ngủ","我想睡觉了。(Wǒ xiǎng shuìjiào le.) - Tôi muốn ngủ rồi."),
    ("做","zuò","làm, nấu","我做饭。(Wǒ zuò fàn.) - Tôi nấu cơm."),
    ("写","xiě","viết","我写汉字。(Wǒ xiě Hànzì.) - Tôi viết chữ Hán."),
    ("住","zhù","sống, ở","我住在河内。(Wǒ zhù zài Hénèi.) - Tôi sống ở Hà Nội."),
    ("坐","zuò","ngồi","请坐！(Qǐng zuò!) - Mời ngồi!"),
    ("走","zǒu","đi bộ, đi","我们走吧！(Wǒmen zǒu ba!) - Chúng ta đi thôi!"),
    ("钱","qián","tiền","这个多少钱？(Zhège duōshǎo qián?) - Cái này bao nhiêu tiền?"),
    ("时间","shíjiān","thời gian","我没有时间。(Wǒ méiyǒu shíjiān.) - Tôi không có thời gian."),
    ("名字","míngzi","tên","你叫什么名字？(Nǐ jiào shénme míngzi?) - Bạn tên là gì?"),
    ("手机","shǒujī","điện thoại di động","我的手机没有电了。(Wǒ de shǒujī méiyǒu diàn le.) - Điện thoại tôi hết pin rồi."),
    ("电脑","diànnǎo","máy tính","我用电脑工作。(Wǒ yòng diànnǎo gōngzuò.) - Tôi dùng máy tính để làm việc."),
    ("汽车","qìchē","xe ô tô","他有一辆汽车。(Tā yǒu yī liàng qìchē.) - Anh ấy có một chiếc ô tô."),
    ("飞机","fēijī","máy bay","我坐飞机去北京。(Wǒ zuò fēijī qù Běijīng.) - Tôi đi máy bay đến Bắc Kinh."),
    ("身体","shēntǐ","cơ thể, sức khỏe","你身体好吗？(Nǐ shēntǐ hǎo ma?) - Sức khỏe của bạn tốt không?"),
    ("头","tóu","đầu","我头疼。(Wǒ tóu téng.) - Tôi đau đầu."),
    ("眼睛","yǎnjīng","mắt","她的眼睛很大。(Tā de yǎnjīng hěn dà.) - Mắt cô ấy rất to."),
    ("手","shǒu","tay","他的手很大。(Tā de shǒu hěn dà.) - Tay anh ấy rất to."),
    ("高兴","gāoxìng","vui vẻ, phấn khởi","我很高兴见到你。(Wǒ hěn gāoxìng jiàn dào nǐ.) - Tôi rất vui được gặp bạn."),
    ("快乐","kuàilè","hạnh phúc, vui vẻ","生日快乐！(Shēngrì kuàilè!) - Chúc mừng sinh nhật!"),
    ("热","rè","nóng","今天很热。(Jīntiān hěn rè.) - Hôm nay rất nóng."),
    ("冷","lěng","lạnh","冬天很冷。(Dōngtiān hěn lěng.) - Mùa đông rất lạnh."),
    ("累","lèi","mệt mỏi","我今天很累。(Wǒ jīntiān hěn lèi.) - Hôm nay tôi rất mệt."),
    ("漂亮","piàoliang","xinh đẹp","她很漂亮。(Tā hěn piàoliang.) - Cô ấy rất xinh đẹp."),
    ("可爱","kě'ài","đáng yêu","这只狗真可爱！(Zhè zhī gǒu zhēn kě'ài!) - Con chó này thật đáng yêu!"),
    ("新","xīn","mới","这是新手机。(Zhè shì xīn shǒujī.) - Đây là điện thoại mới."),
    ("贵","guì","đắt","这个太贵了。(Zhège tài guì le.) - Cái này đắt quá."),
    ("便宜","piányí","rẻ","这里的东西很便宜。(Zhèlǐ de dōngxi hěn piányí.) - Đồ ở đây rất rẻ."),
    ("近","jìn","gần","学校离这里很近。(Xuéxiào lí zhèlǐ hěn jìn.) - Trường gần đây lắm."),
    ("远","yuǎn","xa","超市离这里很远。(Chāoshì lí zhèlǐ hěn yuǎn.) - Siêu thị ở xa đây lắm."),
    ("快","kuài","nhanh","他走得很快。(Tā zǒu de hěn kuài.) - Anh ấy đi rất nhanh."),
    ("慢","màn","chậm","请说慢一点。(Qǐng shuō màn yīdiǎn.) - Hãy nói chậm lại một chút."),
    ("忙","máng","bận","我最近很忙。(Wǒ zuìjìn hěn máng.) - Gần đây tôi rất bận."),
    ("难","nán","khó","这道题很难。(Zhè dào tí hěn nán.) - Bài này rất khó."),
    ("容易","róngyì","dễ dàng","这个很容易。(Zhège hěn róngyì.) - Cái này rất dễ."),
    ("一起","yīqǐ","cùng nhau","我们一起去吧！(Wǒmen yīqǐ qù ba!) - Chúng ta cùng đi nhé!"),
    ("然后","ránhòu","sau đó","先吃饭，然后休息。(Xiān chīfàn, ránhòu xiūxi.) - Ăn cơm trước, sau đó nghỉ ngơi."),
    ("但是","dànshì","nhưng mà","他很忙，但是很快乐。(Tā hěn máng, dànshì hěn kuàilè.) - Anh ấy rất bận nhưng rất vui."),
    ("因为","yīnwèi","vì, bởi vì","因为下雨，我不去了。(Yīnwèi xià yǔ, wǒ bù qù le.) - Vì trời mưa, tôi không đi nữa."),
    ("所以","suǒyǐ","vì vậy, cho nên","我累了，所以要休息。(Wǒ lèi le, suǒyǐ yào xiūxi.) - Tôi mệt rồi, vì vậy muốn nghỉ."),
    ("如果","rúguǒ","nếu như","如果下雨，我不去。(Rúguǒ xià yǔ, wǒ bù qù.) - Nếu trời mưa, tôi không đi."),
    ("已经","yǐjīng","đã rồi","我已经吃了。(Wǒ yǐjīng chī le.) - Tôi đã ăn rồi."),
    ("还","hái","còn, vẫn","我还没吃。(Wǒ hái méi chī.) - Tôi vẫn chưa ăn."),
    ("最","zuì","nhất","他是最高的。(Tā shì zuì gāo de.) - Anh ấy là cao nhất."),
    ("非常","fēicháng","vô cùng, rất","这里非常漂亮。(Zhèlǐ fēicháng piàoliang.) - Nơi này rất đẹp."),
    ("特别","tèbié","đặc biệt, rất","这个特别好吃。(Zhège tèbié hǎochī.) - Cái này đặc biệt ngon."),
    ("真的","zhēnde","thật sự, thật không?","真的吗？(Zhēnde ma?) - Thật không?"),
    ("可能","kěnéng","có thể, có lẽ","他可能来晚了。(Tā kěnéng lái wǎn le.) - Anh ấy có lẽ đến muộn."),
    ("一定","yīdìng","nhất định, chắc chắn","我一定去。(Wǒ yīdìng qù.) - Tôi nhất định sẽ đi."),
    ("应该","yīnggāi","nên, cần phải","你应该多喝水。(Nǐ yīnggāi duō hē shuǐ.) - Bạn nên uống nhiều nước."),
    ("必须","bìxū","phải, bắt buộc","你必须去上课。(Nǐ bìxū qù shàngkè.) - Bạn phải đi học."),
    ("帮","bāng","giúp đỡ","你能帮我吗？(Nǐ néng bāng wǒ ma?) - Bạn có thể giúp tôi không?"),
    ("等","děng","chờ, đợi","请等我。(Qǐng děng wǒ.) - Hãy đợi tôi."),
    ("找","zhǎo","tìm kiếm","我在找我的钥匙。(Wǒ zài zhǎo wǒ de yàoshi.) - Tôi đang tìm chìa khóa của tôi."),
    ("用","yòng","dùng, sử dụng","我用筷子吃饭。(Wǒ yòng kuàizi chīfàn.) - Tôi dùng đũa ăn cơm."),
    ("给","gěi","cho, đưa cho","我给你一本书。(Wǒ gěi nǐ yī běn shū.) - Tôi đưa cho bạn một cuốn sách."),
    ("告诉","gàosu","nói cho biết, bảo","请告诉我。(Qǐng gàosu wǒ.) - Hãy nói cho tôi biết."),
    ("问","wèn","hỏi","我想问一个问题。(Wǒ xiǎng wèn yīgè wèntí.) - Tôi muốn hỏi một câu hỏi."),
    ("准备","zhǔnbèi","chuẩn bị","我在准备考试。(Wǒ zài zhǔnbèi kǎoshì.) - Tôi đang chuẩn bị thi."),
    ("开始","kāishǐ","bắt đầu","我们开始吧！(Wǒmen kāishǐ ba!) - Chúng ta bắt đầu thôi!"),
    ("结束","jiéshù","kết thúc","课结束了。(Kè jiéshù le.) - Buổi học kết thúc rồi."),
    ("完","wán","xong, hết","我吃完了。(Wǒ chī wán le.) - Tôi ăn xong rồi."),
    ("送","sòng","tặng, tiễn","我送你一个礼物。(Wǒ sòng nǐ yīgè lǐwù.) - Tôi tặng bạn một món quà."),
    ("借","jiè","mượn, cho mượn","我可以借你的书吗？(Wǒ kěyǐ jiè nǐ de shū ma?) - Tôi có thể mượn sách của bạn không?"),
    ("游泳","yóuyǒng","bơi lội","我会游泳。(Wǒ huì yóuyǒng.) - Tôi biết bơi."),
    ("运动","yùndòng","vận động, thể dục","我每天运动一小时。(Wǒ měitiān yùndòng yī xiǎoshí.) - Tôi tập thể dục một tiếng mỗi ngày."),
    ("旅游","lǚyóu","du lịch","我喜欢旅游。(Wǒ xǐhuān lǚyóu.) - Tôi thích du lịch."),
    ("音乐","yīnyuè","âm nhạc","我喜欢听音乐。(Wǒ xǐhuān tīng yīnyuè.) - Tôi thích nghe nhạc."),
    ("电影","diànyǐng","phim điện ảnh","今晚看电影吗？(Jīnwǎn kàn diànyǐng ma?) - Tối nay xem phim không?"),
    ("天气","tiānqì","thời tiết","今天天气很好。(Jīntiān tiānqì hěn hǎo.) - Hôm nay thời tiết rất đẹp."),
    ("下雨","xià yǔ","trời mưa","今天下雨了。(Jīntiān xià yǔ le.) - Hôm nay trời mưa rồi."),
    ("春天","chūntiān","mùa xuân","我喜欢春天。(Wǒ xǐhuān chūntiān.) - Tôi thích mùa xuân."),
    ("夏天","xiàtiān","mùa hè","夏天很热。(Xiàtiān hěn rè.) - Mùa hè rất nóng."),
    ("秋天","qiūtiān","mùa thu","秋天很凉快。(Qiūtiān hěn liángkuai.) - Mùa thu rất mát mẻ."),
    ("冬天","dōngtiān","mùa đông","冬天很冷。(Dōngtiān hěn lěng.) - Mùa đông rất lạnh."),
    ("红色","hóngsè","màu đỏ","我喜欢红色。(Wǒ xǐhuān hóngsè.) - Tôi thích màu đỏ."),
    ("蓝色","lánsè","màu xanh dương","天空是蓝色的。(Tiānkōng shì lánsè de.) - Bầu trời màu xanh."),
    ("白色","báisè","màu trắng","雪是白色的。(Xuě shì báisè de.) - Tuyết màu trắng."),
    ("衣服","yīfú","quần áo","这件衣服很漂亮。(Zhè jiàn yīfú hěn piàoliang.) - Bộ quần áo này rất đẹp."),
    ("鞋","xié","giày dép","这双鞋很舒服。(Zhè shuāng xié hěn shūfú.) - Đôi giày này rất thoải mái."),
    ("礼物","lǐwù","quà tặng","生日礼物很好看。(Shēngrì lǐwù hěn hǎokàn.) - Quà sinh nhật rất đẹp."),
    ("护照","hùzhào","hộ chiếu","我的护照在哪里？(Wǒ de hùzhào zài nǎlǐ?) - Hộ chiếu của tôi ở đâu?"),
    ("银行","yínháng","ngân hàng","银行几点关门？(Yínháng jǐ diǎn guānmén?) - Ngân hàng đóng cửa lúc mấy giờ?"),
    ("超市","chāoshì","siêu thị","我去超市买东西。(Wǒ qù chāoshì mǎi dōngxi.) - Tôi đi siêu thị mua đồ."),
    ("公园","gōngyuán","công viên","我在公园跑步。(Wǒ zài gōngyuán pǎobù.) - Tôi chạy bộ ở công viên."),
    ("图书馆","túshūguǎn","thư viện","我去图书馆看书。(Wǒ qù túshūguǎn kàn shū.) - Tôi đến thư viện đọc sách."),
    ("教室","jiàoshì","lớp học","我在教室学习。(Wǒ zài jiàoshì xuéxí.) - Tôi học ở lớp học."),
    ("厨房","chúfáng","nhà bếp","妈妈在厨房做饭。(Māma zài chúfáng zuò fàn.) - Mẹ đang nấu ăn trong bếp."),
    ("窗户","chuānghù","cửa sổ","请打开窗户。(Qǐng dǎkāi chuānghù.) - Hãy mở cửa sổ."),
    ("门","mén","cửa","请关门。(Qǐng guān mén.) - Xin hãy đóng cửa."),
    ("桌子","zhuōzi","cái bàn","书在桌子上。(Shū zài zhuōzi shàng.) - Sách ở trên bàn."),
    ("椅子","yǐzi","cái ghế","请坐在椅子上。(Qǐng zuò zài yǐzi shàng.) - Mời ngồi trên ghế."),
    ("床","chuáng","giường","我的床很舒服。(Wǒ de chuáng hěn shūfú.) - Giường tôi rất thoải mái."),
    ("筷子","kuàizi","đũa","我会用筷子。(Wǒ huì yòng kuàizi.) - Tôi biết dùng đũa."),
    ("钥匙","yàoshi","chìa khóa","我找不到钥匙了。(Wǒ zhǎo bú dào yàoshi le.) - Tôi tìm không thấy chìa khóa."),
    ("票","piào","vé","我买了一张票。(Wǒ mǎi le yī zhāng piào.) - Tôi mua một cái vé."),
    ("地址","dìzhǐ","địa chỉ","你的地址是什么？(Nǐ de dìzhǐ shì shénme?) - Địa chỉ của bạn là gì?"),
    ("问题","wèntí","câu hỏi, vấn đề","你有什么问题？(Nǐ yǒu shénme wèntí?) - Bạn có câu hỏi gì không?"),
    ("计划","jìhuà","kế hoạch","你有什么计划？(Nǐ yǒu shénme jìhuà?) - Bạn có kế hoạch gì không?"),
    ("机会","jīhuì","cơ hội","这是好机会。(Zhè shì hǎo jīhuì.) - Đây là cơ hội tốt."),
    ("故事","gùshi","câu chuyện","请给我讲一个故事。(Qǐng gěi wǒ jiǎng yīgè gùshi.) - Hãy kể cho tôi nghe một câu chuyện."),
    ("汉字","Hànzì","chữ Hán","汉字很难写。(Hànzì hěn nán xiě.) - Chữ Hán rất khó viết."),
    ("考试","kǎoshì","kỳ thi, thi cử","明天有考试。(Míngtiān yǒu kǎoshì.) - Ngày mai có thi."),
    ("作业","zuòyè","bài tập về nhà","我的作业很多。(Wǒ de zuòyè hěn duō.) - Bài tập về nhà của tôi rất nhiều."),
    ("上课","shàngkè","lên lớp, học bài","我们八点上课。(Wǒmen bā diǎn shàngkè.) - Chúng tôi lên lớp lúc 8 giờ."),
    ("上班","shàngbān","đi làm","他每天八点上班。(Tā měitiān bā diǎn shàngbān.) - Anh ấy đi làm lúc 8 giờ mỗi ngày."),
    ("周末","zhōumò","cuối tuần","周末我休息。(Zhōumò wǒ xiūxi.) - Cuối tuần tôi nghỉ ngơi."),
    ("生日","shēngrì","sinh nhật","今天是我的生日。(Jīntiān shì wǒ de shēngrì.) - Hôm nay là sinh nhật tôi."),
    ("孩子","háizi","đứa trẻ, con cái","他们有两个孩子。(Tāmen yǒu liǎng gè háizi.) - Họ có hai đứa con."),
    ("医生","yīshēng","bác sĩ","医生说我很健康。(Yīshēng shuō wǒ hěn jiànkāng.) - Bác sĩ nói tôi rất khỏe mạnh."),
    ("爷爷","yéye","ông nội","爷爷每天早上锻炼。(Yéye měitiān zǎoshàng duànliàn.) - Ông nội mỗi buổi sáng tập thể dục."),
    ("奶奶","nǎinai","bà nội","奶奶做的饭很好吃。(Nǎinai zuò de fàn hěn hǎochī.) - Cơm bà nội nấu rất ngon."),
    ("照片","zhàopiàn","ảnh chụp","这张照片很好看。(Zhè zhāng zhàopiàn hěn hǎokàn.) - Bức ảnh này rất đẹp."),
    ("颜色","yánsè","màu sắc","你喜欢什么颜色？(Nǐ xǐhuān shénme yánsè?) - Bạn thích màu gì?"),
    ("声音","shēngyīn","âm thanh, giọng nói","他的声音很好听。(Tā de shēngyīn hěn hǎotīng.) - Giọng anh ấy rất hay."),
    ("结婚","jiéhūn","kết hôn","他们去年结婚了。(Tāmen qùnián jiéhūn le.) - Họ đã kết hôn năm ngoái."),
    ("丈夫","zhàngfu","chồng","她的丈夫是医生。(Tā de zhàngfu shì yīshēng.) - Chồng cô ấy là bác sĩ."),
    ("妻子","qīzi","vợ","我妻子很聪明。(Wǒ qīzi hěn cōngming.) - Vợ tôi rất thông minh."),
]


# ── State helpers ──────────────────────────────────────────
def load_state():
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    indices = list(range(len(VOCAB)))
    random.shuffle(indices)
    return {"remaining": indices, "done": [], "cycle": 1}


def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def pick_words(state, n=WORDS_PER_DAY):
    if len(state["remaining"]) < n:
        leftover = state["remaining"][:]
        leftover_set = set(leftover)
        new_pool = [i for i in range(len(VOCAB)) if i not in leftover_set]
        random.shuffle(new_pool)
        state["done"] = []
        state["remaining"] = leftover + new_pool
        state["cycle"] += 1
    chosen = state["remaining"][:n]
    state["remaining"] = state["remaining"][n:]
    state["done"].extend(chosen)
    return chosen


def esc(s):
    for c in r"\_*[]()~`>#+-=|{}.!":
        s = s.replace(c, f"\\{c}")
    return s


# ── Message builder ────────────────────────────────────────
def build_message(indices, state):
    total = len(VOCAB)
    done_count = len(state["done"])
    pct = int(done_count / total * 100)
    bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))

    now_vn = datetime.now(TIMEZONE)
    session = "🌅 Buổi sáng" if now_vn.hour < 12 else "🌙 Buổi tối"
    date_str = now_vn.strftime("%d/%m/%Y")

    lines = [
        f"🇨🇳 *HSK 1\\-2 \\| {session} \\| {date_str}*",
        f"📚 Vòng \\#{state['cycle']} — Tiến độ: {done_count}/{total} từ \\({pct}%\\)",
        f"`{bar}`",
        "",
        "━━━━━━━━━━━━━━━━━━",
    ]
    for rank, idx in enumerate(indices, 1):
        hanzi, pinyin, meaning, example = VOCAB[idx]
        lines += [
            "",
            f"*{rank}\\. {esc(hanzi)}*  \\|  _{esc(pinyin)}_",
            f"📖 {esc(meaning)}",
            f"💬 {esc(example)}",
        ]
    lines += [
        "",
        "━━━━━━━━━━━━━━━━━━",
        "💪 *加油\\!* Học đều mỗi ngày sẽ thành công\\! 🎯",
    ]
    return "\n".join(lines)


# ── Telegram sender ────────────────────────────────────────
async def send_telegram(text: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "MarkdownV2"}
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(url, json=payload)
        if not r.is_success:
            print(f"Telegram error {r.status_code}: {r.text}")
        r.raise_for_status()
    now_str = datetime.now(TIMEZONE).strftime("%H:%M:%S")
    print(f"[{now_str}] ✅ Gửi thành công!")


async def job():
    state = load_state()
    chosen = pick_words(state)
    msg = build_message(chosen, state)
    await send_telegram(msg)
    save_state(state)


def escape_markdown_v2(text: str) -> str:
    for c in r"\_*[]()~`>#+-=|{}.!":
        text = text.replace(c, f"\\{c}")
    return text


async def send_deployment_notification():
    text = (
        "HSK bot deployment notice\n"
        f"Time: {datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Schedule: {', '.join(SCHEDULE_TIMES)}\n"
        f"Words per send: {WORDS_PER_DAY}"
    )
    await send_telegram(escape_markdown_v2(text))


# ── Scheduler ──────────────────────────────────────────────
async def main():
    print("🤖 HSK Reminder Bot khởi động — múi giờ Asia/Ho_Chi_Minh")
    print(f"⏰ Lịch gửi: {', '.join(SCHEDULE_TIMES)}  |  {WORDS_PER_DAY} từ/lần")

    try:
        await send_deployment_notification()
    except Exception as e:
        print(f"❌ Deployment notification failed: {e}")

    sent_today: set[str] = set()
    current_date = datetime.now(TIMEZONE).strftime("%Y-%m-%d")

    while True:
        now_vn = datetime.now(TIMEZONE)
        hhmm = now_vn.strftime("%H:%M")
        date_key = now_vn.strftime("%Y-%m-%d")

        if date_key != current_date:
            sent_today.clear()
            current_date = date_key

        slot_key = f"{date_key}_{hhmm}"
        if hhmm in SCHEDULE_TIMES and slot_key not in sent_today:
            print(f"\n[{hhmm}] 🔔 Đến giờ gửi!")
            try:
                await job()
                sent_today.add(slot_key)
            except Exception as e:
                print(f"❌ Lỗi: {e}")

        await asyncio.sleep(20)


if __name__ == "__main__":
    asyncio.run(main())
