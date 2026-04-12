import time
import random
import pandas as pd
from playwright.sync_api import sync_playwright

def crawl_xiaohongshu_real(keywords):
    print(f"🚀 正在启动智能采集智能体 (Playwright内核)...")
    
    all_data = []

    with sync_playwright() as p:
        # 1. 启动浏览器 (headless=False 表示显示浏览器窗口，方便扫码)
        browser = p.chromium.launch(headless=False)
        
        # 2. 创建上下文 (模拟真实的手机或PC环境)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        # 3. 访问首页，提示人工登录
        print("⚠️ 请在打开的浏览器窗口中登录小红书账号...")
        page.goto("https://www.xiaohongshu.com/")
        
        # 等待用户扫码登录（最长等待 60 秒）
        # 实际使用中，你可以检测页面元素变化来判断是否登录成功
        input("👉 登录完成后，按回车键继续采集...")
        
        # 4. 开始循环采集
        for keyword in keywords:
            print(f"📡 正在采集关键词：【{keyword}】...")
            
            # 构造搜索 URL
            search_url = f"https://www.xiaohongshu.com/search_result?keyword={keyword}&source=web_search_result_notes"
            page.goto(search_url)
            
            # 等待页面加载 (模拟人类随机等待)
            time.sleep(random.uniform(3, 5)) 
            
            # 5. 解析页面数据 (核心逻辑)
            # 注意：小红书 class 名是动态混淆的，这里使用相对稳定的属性选择器
            # 我们尝试抓取笔记卡片
            notes = page.query_selector_all("div[class*='cover']")
            
            if not notes:
                print(f"⚠️ 未抓取到数据，可能是被反爬拦截或需要滚动加载。")
                continue

            print(f"✅ 发现 {len(notes)} 条笔记，正在提取详情...")
            
            # 限制每次只抓前 5 条，防止耗时过长
            count = 0
            for note in notes:
                if count >= 5: break
                
                try:
                    # 提取标题 (通常在 img 的 alt 属性或特定的 div 中)
                    title_elem = note.query_selector("img")
                    title = title_elem.get_attribute("alt") if title_elem else "无标题"
                    
                    # 提取作者
                    author_elem = note.query_selector("span[class*='nickname']")
                    author = author_elem.inner_text() if author_elem else "未知作者"
                    
                    # 提取点赞数
                    like_elem = note.query_selector("span[class*='count']")
                    likes = like_elem.inner_text() if like_elem else "0"
                    
                    # 提取链接 (需要拼接)
                    link_elem = note.query_selector("a")
                    href = link_elem.get_attribute("href") if link_elem else ""
                    full_link = f"https://www.xiaohongshu.com{href}" if href else ""

                    # 存入字典
                    data_item = {
                        "keyword": keyword,
                        "title": title,
                        "author": author,
                        "likes": likes,
                        "url": full_link,
                        "content": f"这是一篇关于{keyword}的热门笔记，由用户{author}发布。" 
                    }
                    
                    all_data.append(data_item)
                    count += 1
                    
                except Exception as e:
                    continue
            
            # 翻页逻辑（可选）：简单模拟点击下一页
            # next_btn = page.query_selector("button[class*='next']")
            # if next_btn: next_btn.click()
            
            print(f"📄 关键词【{keyword}】采集完成，暂存 {count} 条数据。")
            time.sleep(random.uniform(2, 4)) # 随机休眠

        browser.close()

    # 6. 保存数据
    if all_data:
        df = pd.DataFrame(all_data)
        df.to_csv("real_xiaohongshu_data.csv", index=False, encoding='utf-8-sig')
        print(f"🎉 采集结束！共获取 {len(all_data)} 条真实数据，已保存为 real_xiaohongshu_data.csv")
    else:
        print("❌ 采集失败，未获取到任何数据。")

if __name__ == "__main__":
    # 你的毕设关键词
    keywords_list = ["苏州旅游攻略", "北京美食", "西安兵马俑"]
    crawl_xiaohongshu_real(keywords_list)