# agent.py
import os
import re
import json
import time
import pandas as pd
from dotenv import load_dotenv
from dashscope import Generation
import dashscope
from typing import Generator, List, Tuple

CHINESE_CITIES = [
        "北京", "天津", "上海", "重庆",
        "石家庄", "唐山", "秦皇岛", "邯郸", "邢台", "保定", "张家口", "承德", "沧州", "廊坊", "衡水",
        "太原", "大同", "阳泉", "长治", "晋城", "朔州", "晋中", "运城", "忻州", "临汾", "吕梁",
        "呼和浩特", "包头", "乌海", "赤峰", "通辽", "鄂尔多斯", "呼伦贝尔", "巴彦淖尔", "乌兰察布",
        "沈阳", "大连", "鞍山", "抚顺", "本溪", "丹东", "锦州", "营口", "阜新", "辽阳", "盘锦", "铁岭", "朝阳", "葫芦岛",
        "长春", "吉林", "四平", "辽源", "通化", "白山", "松原", "白城", "延边",
        "哈尔滨", "齐齐哈尔", "鸡西", "鹤岗", "双鸭山", "大庆", "伊春", "佳木斯", "七台河", "牡丹江", "黑河", "绥化", "大兴安岭",
        "南京", "无锡", "徐州", "常州", "苏州", "南通", "连云港", "淮安", "盐城", "扬州", "镇江", "泰州", "宿迁",
        "杭州", "宁波", "温州", "嘉兴", "湖州", "绍兴", "金华", "衢州", "舟山", "台州", "丽水",
        "合肥", "芜湖", "蚌埠", "淮南", "马鞍山", "淮北", "铜陵", "安庆", "黄山", "滁州", "阜阳", "宿州", "六安", "亳州", "池州", "宣城",
        "福州", "厦门", "莆田", "三明", "泉州", "漳州", "南平", "龙岩", "宁德",
        "南昌", "景德镇", "萍乡", "九江", "新余", "鹰潭", "赣州", "吉安", "宜春", "抚州", "上饶",
        "济南", "青岛", "淄博", "枣庄", "东营", "烟台", "潍坊", "济宁", "泰安", "威海", "日照", "临沂", "德州", "聊城", "滨州", "菏泽",
        "郑州", "开封", "洛阳", "平顶山", "安阳", "鹤壁", "新乡", "焦作", "濮阳", "许昌", "漯河", "三门峡", "南阳", "商丘", "信阳", "周口", "驻马店",
        "武汉", "黄石", "十堰", "宜昌", "襄阳", "鄂州", "荆门", "孝感", "荆州", "黄冈", "咸宁", "随州", "恩施",
        "长沙", "株洲", "湘潭", "衡阳", "邵阳", "岳阳", "常德", "张家界", "益阳", "郴州", "永州", "怀化", "娄底", "湘西",
        "广州", "韶关", "深圳", "珠海", "汕头", "佛山", "江门", "湛江", "茂名", "肇庆", "惠州", "梅州", "汕尾", "河源", "阳江", "清远", "东莞", "中山", "潮州", "揭阳", "云浮",
        "南宁", "柳州", "桂林", "梧州", "北海", "防城港", "钦州", "贵港", "玉林", "百色", "贺州", "河池", "来宾", "崇左",
        "海口", "三亚", "三沙", "儋州",
        "成都", "自贡", "攀枝花", "泸州", "德阳", "绵阳", "广元", "遂宁", "内江", "乐山", "南充", "眉山", "宜宾", "广安", "达州", "雅安", "巴中", "资阳", "阿坝", "甘孜", "凉山",
        "贵阳", "六盘水", "遵义", "安顺", "毕节", "铜仁", "黔西南", "黔东南", "黔南",
        "昆明", "曲靖", "玉溪", "保山", "昭通", "丽江", "普洱", "临沧", "楚雄", "红河", "文山", "西双版纳", "大理", "德宏", "怒江", "迪庆",
        "拉萨", "日喀则", "昌都", "林芝", "山南", "那曲", "阿里",
        "西安", "铜川", "宝鸡", "咸阳", "渭南", "延安", "汉中", "榆林", "安康", "商洛",
        "兰州", "嘉峪关", "金昌", "白银", "天水", "武威", "张掖", "平凉", "酒泉", "庆阳", "定西", "陇南", "临夏", "甘南",
        "西宁", "海东", "海北", "黄南", "海南", "果洛", "玉树", "海西",
        "银川", "石嘴山", "吴忠", "固原", "中卫",
        "乌鲁木齐", "克拉玛依", "吐鲁番", "哈密", "昌吉", "博尔塔拉", "巴音郭楞", "阿克苏", "克孜勒苏", "喀什", "和田", "伊犁", "塔城", "阿勒泰"
    ]

# ========== 新增：热门景点关键词库（用于演示，可自行扩充）==========
SCENIC_SPOTS = {
    "北京": ["故宫", "天坛", "颐和园", "长城", "鸟巢"],
    "上海": ["外滩", "东方明珠", "迪士尼", "豫园", "南京路"],
    "杭州": ["西湖", "灵隐寺", "千岛湖", "宋城", "雷峰塔"],
    "苏州": ["拙政园", "留园", "虎丘", "周庄", "同里"],
    "西安": ["兵马俑", "大雁塔", "华清池", "城墙", "回民街"],
    "成都": ["宽窄巷子", "锦里", "大熊猫基地", "青城山", "都江堰"],
    # ... 可以根据你的行程库内容继续添加
}
# =====================================

load_dotenv()
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

# 加载行程库
try:
    ROUTES_DF = pd.read_csv("travel_routes.csv", encoding="utf-8")
except Exception as e:
    print(f"加载 travel_routes.csv 失败: {e}")
    ROUTES_DF = pd.DataFrame(columns=["city", "days", "route"])

# ========== 新增：加载本地美食库 ==========
try:
    CUISINE_DF = pd.read_csv("local_cuisine.csv", encoding="utf-8")
except Exception as e:
    print(f"加载 local_cuisine.csv 失败: {e}")
    CUISINE_DF = pd.DataFrame(columns=["city", "food"])
# ======================================

def is_itinerary_query(query: str) -> bool:
    """判断是否为行程规划请求"""
    # 包含中国所有地级市的完整列表 (共300+个城市)
    city_pattern = "|".join(CHINESE_CITIES)
    rule1 = bool(re.search(r'(.*?)[一二三四五六七八九十\d]+[天日](游|行程|攻略|计划)', query))
    rule2 = bool(re.search(fr'({city_pattern}).*(规划|安排|玩|旅游).*([一二三四五六七八九十\d]+天|几日|几天)', query))
    rule3 = bool(re.search(fr'({city_pattern})[一二三四五六七八九十\d]+日?玩', query))
    rule4 = bool(re.search(fr'帮我.*规划.*({city_pattern}).*(行程|旅游|玩)', query))
    return rule1 or rule2 or rule3 or rule4

# ========== 新增：判断是否为美食查询 ==========
def is_food_query(query: str) -> bool:
    """判断是否为美食推荐请求"""
    food_keywords = ["美食", "好吃", "吃", "推荐吃的", "有什么吃的", "特色", "必吃", "小吃"]
    return any(kw in query for kw in food_keywords)
# ======================================

def extract_city_and_days(query: str) -> Tuple[str, int]:
    """从查询中提取城市和天数"""
    cities = CHINESE_CITIES
    city = None
    for c in cities:
        if c in query:
            city = c
            break
    
    days = 3
    if match := re.search(r'(\d+)[天日]', query):
        days = int(match.group(1))
    elif match := re.search(r'([一二三四五六七八九十两])[天日]', query):
        cn_map = {"一":1,"二":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9,"十":10,"两":2}
        days = cn_map.get(match.group(1), 3)
    elif re.search(r'几日|几天', query):
        days = 3
    
    return city, days

# ========== 核心修改：新函数用于查找所有匹配的路线 ==========
def find_all_matching_routes(city: str, days: int) -> List[Tuple[str, int]]:
    """
    查找指定城市的所有匹配路线。
    优先级: 1. 精确匹配 (城市+天数) > 2. 模糊匹配 (仅城市)
    返回: [(route_text, actual_days), ...]
    """
    if ROUTES_DF.empty:
        return []
    # 1. 尝试精确匹配：城市 + 天数
    exact_matches = ROUTES_DF[(ROUTES_DF["city"] == city) & (ROUTES_DF["days"] == days)]
    if not exact_matches.empty:
        return [(row["route"], row["days"]) for _, row in exact_matches.iterrows()]
    # 2. 如果没有精确匹配，则返回该城市所有的路线
    city_matches = ROUTES_DF[ROUTES_DF["city"] == city]
    if not city_matches.empty:
        return [(row["route"], row["days"]) for _, row in city_matches.iterrows()]
    return []

# ========== 获取本地美食推荐的方法 ==========
def get_local_food_recommendation(city: str) -> str:
    if CUISINE_DF.empty or not city:
        return ""
    
    city_data = CUISINE_DF[CUISINE_DF['city'] == city]
    if city_data.empty:
        return f"很抱歉，我的美食库中暂时没有 {city} 的相关推荐。"
    response_parts = [f"为您精心整理了 **{city}** 的特色美食攻略：\n"]
    # 先列出所有菜系
    cuisines = city_data[city_data['type'] == '菜系']
    if not cuisines.empty:
        for category in cuisines['category'].unique():
            response_parts.append(f"\n**【{category}】**")
            for _, row in cuisines[cuisines['category'] == category].iterrows():
                response_parts.append(f"- **{row['name']}**: {row['description']}")
    # 再统一列出所有店铺（不分菜系）
    shops = city_data[city_data['type'] == '店铺']
    if not shops.empty:
        response_parts.append(f"\n**【{city}美食地标推荐】**")
        for _, row in shops.iterrows():
            response_parts.append(f"- **{row['name']}**: {row['description']}")
    response_parts.append(f"\n希望这份美食指南能让您的 **{city}** 之旅更加精彩！祝您用餐愉快！😊")
    return "\n".join(response_parts)
# =========================================

# ========== 核心修改：解析预订意图 =========
def parse_booking_intent(query: str) -> dict:
    """解析预订意图，返回类型和可能的实体"""
    intent = {"type": "hotel", "entity": None}  # 默认为酒店
    
    # 判断预订类型
    if any(kw in query for kw in ["酒店", "住宿", "住", "民宿"]):
        intent["type"] = "hotel"
    elif any(kw in query for kw in ["机票", "飞机", "飞往", "航班", "坐飞机"]):
        intent["type"] = "flight"
    elif any(kw in query for kw in ["火车票", "高铁", "动车", "坐火车"]):
        intent["type"] = "train"
    # ... 可以继续扩展其他类型
    
    # 尝试提取更具体的地点，比如景点名
    for city, spots in SCENIC_SPOTS.items():
        for spot in spots:
            if spot in query:
                intent["entity"] = spot
                break
        if intent["entity"]:
            break
    
    return intent
# =========================================

# ========== 核心修改：生成更精准的携程链接 =========
def generate_ctrip_link(city: str, booking_intent: dict) -> str:
    """
    根据城市名和预订意图，生成一个指向携程的预填充链接。
    """
    import urllib.parse
    
    # 城市ID映射
    city_map = {
        "北京": "beijing2",
        "上海": "shanghai2",
        "广州": "guangzhou3",
        "深圳": "shenzhen4",
        "杭州": "hangzhou17",
        "苏州": "suzhou15",
        "成都": "chengdu8",
        "重庆": "chongqing9",
        "西安": "xian20",
        "厦门": "xiamen19",
        "青岛": "qingdao13",
        "桂林": "guilin26",
        "敦煌": "dunhuang127",
        "南京": "nanjing12",
        "长沙": "changsha18",
        "大连": "dalian14",
        "昆明": "kunming24",
        "哈尔滨": "haerbin21",
        "武汉":"wuhan477"
        # ... 可以根据需要继续添加更多城市的映射
    }
    city_id = city_map.get(city, "beijing2") # 默认跳转北京
    
    if booking_intent["type"] == "hotel":
        # 如果有具体景点，尝试构建包含关键词的搜索URL
        if booking_intent["entity"]:
            # 对实体进行URL编码
            encoded_entity = urllib.parse.quote(booking_intent["entity"])
            # 构建搜索页URL
            return f"https://www.ctrip.com/search?keyword={city}{encoded_entity}&type=hotel"
        else:
            # 否则跳转到城市酒店列表页
            return f"https://hotels.ctrip.com/hotel/{city_id}"
    
    elif booking_intent["type"] == "flight":
        # 更完整的城市三字码映射 (IATA Code)
        flight_city_codes = {
            "北京": "BJS", "上海": "SHA", "广州": "CAN", "深圳": "SZX",
            "杭州": "HGH", "成都": "CTU", "西安": "XIY", "厦门": "XMN",
            "重庆": "CKG", "昆明": "KMG", "南京": "NKG", "青岛": "TAO",
            "大连": "DLC", "哈尔滨": "HRB", "三亚": "SYX", "乌鲁木齐": "URC",
            "桂林": "KWL", "长沙": "CSX", "武汉": "WUH", "郑州": "CGO",
            "天津": "TSN", "福州": "FOC", "济南": "TNA", "合肥": "HFE",
            "南昌": "KHN", "贵阳": "KWE", "兰州": "LHW", "西宁": "XNN",
            "银川": "INC", "海口": "HAK", "呼和浩特": "HET", "长春": "CGQ",
            "石家庄": "SJW", "太原": "TYN", "沈阳": "SHE", "南宁": "NNG"
            # ... 可以根据需要继续补充
        }
        
        # 获取三字码，如果找不到，默认用北京(BJS)
        arrival_code = flight_city_codes.get(city, "BJS")
        
        # 设置一个默认的未来日期 (例如明天)
        from datetime import datetime, timedelta
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # 构建更准确的机票搜索URL
        return f"https://flights.ctrip.com/online/list?DCity1=&ACity1={arrival_code}&SearchType=S&DDate1={tomorrow}"
    
    elif booking_intent["type"] == "train":
        # 跳转到火车票搜索页
        return f"https://trains.ctrip.com/TrainBooking/Search?to={urllib.parse.quote(city)}"
    
    # 默认情况
    return f"https://hotels.ctrip.com/hotel/{city_id}"
# =========================================

def is_booking_intent(query: str) -> bool:
    """判断用户是否有预订意图"""
    keywords = ["订", "预定", "预订", "买票", "下单", "报名"]
    return any(kw in query for kw in keywords)

class TravelAgent:
    def __init__(self):
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        self.chat_history = []
        if not self.api_key:
            raise ValueError("请在 .env 文件中设置 DASHSCOPE_API_KEY")

    def _generate_multi_route_prompt(self, user_input: str, routes: List[Tuple[str, int]]) -> str:
        """构建一个多方案提示词"""
        if not routes:
            return f"用户询问：{user_input}。但本地行程库中没有找到相关数据，请基于你的知识给出一个通用建议。"

        # 构建路线描述
        routes_description = ""
        for i, (route, actual_days) in enumerate(routes, 1):
            routes_description += f"\n方案{i} ({actual_days}天行程):\n{route}\n"
        
        prompt = (
            f"你是一个专业的AI旅行规划师。用户的需求是：'{user_input}'。\n"
            f"我们从本地行程库中找到了{len(routes)}个相关方案供用户选择：\n"
            f"{routes_description}\n"
            "请根据以上信息，为用户生成一个热情、详细且结构清晰的回复：\n"
            "1. 开头要友好地打招呼，并说明找到了多个方案。\n"
            "2. 对每个方案进行生动、具体的介绍，可以补充交通、美食或小贴士，但不要编造原始行程中没有的核心景点。\n"
            "3. 如果某个方案的天数与用户要求的不一致，请说明如何调整（例如，如何压缩或扩展行程）。\n"
            "4. 结尾可以给出一个简单的选择建议，帮助用户决策。\n"
            "5. 整体语气要像朋友聊天一样亲切自然，避免机械感。"
        )
        return prompt

    def clear_history(self):
        """清空对话历史记录"""
        self.chat_history = [] # 将历史记录重置为空列表

    def chat_stream(self, user_input: str, chat_history: list) -> Generator[str, None, None]:
        """
        流式生成回答。
        :param user_input: 用户最新的输入
        :param chat_history: 完整的历史消息
        """

        destination, days = extract_city_and_days(user_input)
        
        # Step 1: 首先检查是否为预订意图
        has_booking_intent = is_booking_intent(user_input)
        final_destination = destination
        
        # 如果当前输入没有城市，但有预订意图，则尝试从历史中找
        if has_booking_intent and not final_destination:
            def extract_destination_from_history(history: list) -> str:
                for msg in reversed(history):
                    if msg["role"] == "user":
                        city, _ = extract_city_and_days(msg["content"])
                        if city:
                            return city
                return None
            final_destination = extract_destination_from_history(chat_history)
        
        if has_booking_intent:
            # 先流式输出固定的提示语
            prompt_message = "抱歉我不能直接帮你下单，但我可以为你提供直接进入携程预订的网页链接。"
            for char in prompt_message:
                yield char
                time.sleep(0.01)
            
            # 然后判断是否有目的地，决定是否提供链接
            if final_destination:
                booking_intent = parse_booking_intent(user_input) 
                ctrip_link = generate_ctrip_link(final_destination, booking_intent) 
                link_payload = {"link": ctrip_link}
                yield "__CTIP_LINK__" + json.dumps(link_payload)
            else:
                # 如果没有目的地，再补充一句提示
                follow_up = "\n为了给您提供更精准的链接，请告诉我您想去哪个城市？"
                for char in follow_up:
                    yield char
                    time.sleep(0.01)
            return # 处理完预订意图后直接返回，不再执行其他逻辑
        # Step 2: 如果不是预订意图，再检查是否为美食查询
        if is_food_query(user_input) and destination:
            ai_text_response = get_local_food_recommendation(destination)
        elif is_itinerary_query(user_input) and destination:
            # 如果是行程查询，走原有逻辑
            all_routes = find_all_matching_routes(destination, days)
            multi_route_prompt = self._generate_multi_route_prompt(user_input, all_routes)
            
            system_prompt_content = "你是一个热情、专业的AI旅行规划师。请像朋友聊天一样，语气亲切自然。最后可以加一个旅行小贴士💡。"
            messages_for_ai = [{"role": "system", "content": system_prompt_content}]
            messages_for_ai.extend(chat_history)
            messages_for_ai.append({"role": "user", "content": multi_route_prompt})
            
            try:
                response = Generation.call(
                    model="qwen-plus",
                    api_key=self.api_key,
                    messages=messages_for_ai,
                    result_format="message"
                )
                ai_text_response = response.output.choices[0].message.content
            except Exception as e:
                ai_text_response = f"AI生成出错: {str(e)}。您可以稍后重试。"
        else:
            # 其他通用查询，交给大模型处理
            system_prompt_content = "你是一个热情、专业的AI旅行规划师。请像朋友聊天一样，语气亲切自然。最后可以加一个旅行小贴士💡。"
            messages_for_ai = [{"role": "system", "content": system_prompt_content}]
            messages_for_ai.extend(chat_history)
            messages_for_ai.append({"role": "user", "content": user_input})
            
            try:
                response = Generation.call(
                    model="qwen-plus",
                    api_key=self.api_key,
                    messages=messages_for_ai,
                    result_format="message"
                )
                ai_text_response = response.output.choices[0].message.content
            except Exception as e:
                ai_text_response = f"AI生成出错: {str(e)}。您可以稍后重试。"
        # ======================================
        
        # 流式输出文本
        for char in ai_text_response:
            yield char
            time.sleep(0.01)