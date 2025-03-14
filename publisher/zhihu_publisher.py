import sys

import pyperclip
from selenium.webdriver import Keys, ActionChains
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import wait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.relative_locator import locate_with
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support.ui import Select

from publisher.common_handler import wait_login
from utils.file_utils import read_file_with_footer, convert_md_to_html, read_file, parse_front_matter, download_image
from utils.selenium_utils import get_html_web_content
from utils.yaml_file_utils import read_jianshu, read_common, read_segmentfault, read_oschina, read_zhihu
import time


def zhihu_publisher(driver,content=None):
    zhihu_config = read_zhihu()
    common_config = read_common()
    if content:
        common_config['content'] = content

    # 提取markdown文档的front matter内容：
    front_matter = parse_front_matter(common_config['content'])

    auto_publish = common_config['auto_publish']

    # driver.switch_to.window(driver.window_handles[0])
    # 打开新标签页并切换到新标签页
    driver.switch_to.new_window('tab')

    # 浏览器实例现在可以被重用，进行你的自动化操作
    driver.get(zhihu_config['site'])
    time.sleep(2)  # 等待2秒

    # 文章标题
    wait_login(driver, By.XPATH,
               '//textarea[contains(@placeholder, "请输入标题")]')
    title = driver.find_element(By.XPATH, '//textarea[contains(@placeholder, "请输入标题")]')
    title.clear()
    if 'title' in front_matter and front_matter['title']:
        title.send_keys(front_matter['title'])
    else:
        title.send_keys(common_config['title'])
    time.sleep(2)  # 等待3秒

    # 文章内容 html版本
    content_file = common_config['content']
    # 注意，zhihu 不能识别转换过后的代码块格式
    content_file_html = convert_md_to_html(content_file)
    get_html_web_content(driver, content_file_html)
    time.sleep(2)  # 等待2秒
    driver.switch_to.window(driver.window_handles[-1])
    time.sleep(1)  # 等待1秒
    # 用的是CodeMirror,不能用元素赋值的方法，所以我们使用拷贝的方法
    cmd_ctrl = Keys.COMMAND if sys.platform == 'darwin' else Keys.CONTROL
    action_chains = webdriver.ActionChains(driver)
    # tab---tab 不好用
    # action_chains.key_down(Keys.TAB).key_up(Keys.TAB).perform()
    # time.sleep(2)
    # 点击内容元素
    content_element = driver.find_element(By.XPATH,
                                          '//div[@class="DraftEditor-editorContainer"]//div[@class="public-DraftStyleDefault-block public-DraftStyleDefault-ltr"]')
    content_element.click()
    time.sleep(2)
    # 模拟实际的粘贴操作
    action_chains.key_down(cmd_ctrl).send_keys('v').key_up(cmd_ctrl).perform()
    time.sleep(3)  # 等待3秒 不需要进行图片解析

    ActionChains(driver).scroll_by_amount(0, 800).perform()
    # 添加封面
    if 'image' in front_matter and front_matter['image']:
        file_input = driver.find_element(By.XPATH, "//input[@type='file' and @class='UploadPicture-input']")
        # 文件上传不支持远程文件上传，所以需要把图片下载到本地
        file_input.send_keys(download_image(front_matter['image']))
        time.sleep(2)

    # 投稿至问题
    # TODO

    # 文章话题
    try:
        # 点击添加话题按钮
        add_topic_button = driver.find_element(By.XPATH, '//button[contains(text(), "添加话题")]')
        add_topic_button.click()
        time.sleep(2)
        
        # 在搜索框中输入"人工智能"
        topic_search_input = driver.find_element(By.XPATH, '//input[@placeholder="搜索话题..."]')
        topic_search_input.send_keys("人工智能")
        time.sleep(3)  # 增加等待时间，确保下拉菜单完全加载
        
        # 尝试多种方式选择下拉菜单中的第一个"人工智能"选项
        try:
            # 方法1: 尝试直接点击包含"人工智能"文本的按钮
            topic_buttons = driver.find_elements(By.XPATH, '//button[contains(text(), "人工智能") and contains(@class, "css-gfrh4c")]')
            if topic_buttons:
                driver.execute_script("arguments[0].click();", topic_buttons[0])
                print("成功选择话题：使用按钮文本方法")
            else:
                # 方法2: 尝试点击下拉菜单中的第一个选项
                dropdown_options = driver.find_elements(By.XPATH, '//div[contains(@class, "Popover-content")]//button')
                if dropdown_options:
                    driver.execute_script("arguments[0].click();", dropdown_options[0])
                    print("成功选择话题：使用下拉菜单第一项方法")
                else:
                    # 方法3: 如果上述方法都失败，尝试按回车键确认第一个选项
                    topic_search_input.send_keys(Keys.RETURN)
                    print("成功选择话题：使用回车键方法")
        except Exception as inner_e:
            print(f"选择话题选项失败: {str(inner_e)}")
            # 备选方案：按回车键
            topic_search_input.send_keys(Keys.RETURN)
            print("使用回车键确认话题选择")
            
        time.sleep(2)
    except Exception as e:
        print(f"添加话题失败: {str(e)}")

    # 专栏收录
    # 选择"不发布到专栏"选项
    no_column_option = driver.find_element(By.XPATH, '//label[@for="PublishPanel-columnLabel-0"]')
    ActionChains(driver).click(no_column_option).perform()
    time.sleep(1)  # 给点时间让选择生效

    # 确认发布
    if auto_publish:
        confirm_button = driver.find_element(By.XPATH, '//button[contains(text(), "发布")]')
        confirm_button.click()

    time.sleep(2)
