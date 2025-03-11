import os.path
import sys
import time
import traceback

import pyperclip
import selenium
from selenium import webdriver
from selenium.webdriver import Keys, ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from publisher.common_handler import wait_login
from utils.file_utils import read_file_with_footer, parse_front_matter, download_image, list_files, write_to_file, read_head, read_file_lines
from utils.yaml_file_utils import read_common, read_csdn

last_published_file_name = 'last_published_csdn.txt'

def csdn_publisher(driver, content=None):
    csdn_config = read_csdn()
    common_config = read_common()
    if content:
        common_config['content'] = content
    auto_publish = common_config['auto_publish']
    # 提取markdown文档的front matter内容：
    front_matter = parse_front_matter(common_config['content'])

    # 打开新标签页并切换到新标签页
    driver.switch_to.new_window('tab')

    # 浏览器实例现在可以被重用，进行你的自动化操作
    driver.get(csdn_config['site'])
    time.sleep(2)  # 等待2秒

    # 文章标题
    wait_login(driver, By.XPATH, '//div[contains(@class,"article-bar")]//input[contains(@placeholder,"请输入文章标题")]')
    title = driver.find_element(By.XPATH, '//div[contains(@class,"article-bar")]//input[contains(@placeholder,"请输入文章标题")]')
    title.clear()
    if 'title' in front_matter and front_matter['title']:
        title.send_keys(front_matter['title'])
    else:
        title.send_keys(common_config['title'])
    time.sleep(2)  # 等待2秒

    # 文章内容 markdown版本
    file_content = read_file_with_footer(common_config['content'])
    # 用的是CodeMirror,不能用元素赋值的方法，所以我们使用拷贝的方法
    cmd_ctrl = Keys.COMMAND if sys.platform == 'darwin' else Keys.CONTROL
    # 将要粘贴的文本内容复制到剪贴板
    pyperclip.copy(file_content)
    action_chains = webdriver.ActionChains(driver)
    content = driver.find_element(By.XPATH, '//div[@class="editor"]//div[@class="cledit-section"]')
    content.click()
    time.sleep(2)
    # 模拟实际的粘贴操作
    action_chains.key_down(cmd_ctrl).send_keys('v').key_up(cmd_ctrl).perform()
    time.sleep(3)  # 等待3秒

    # 发布文章
    send_button = driver.find_element(By.XPATH, '//button[contains(@class, "btn-publish") and contains(text(),"发布文章")]')
    send_button.click()
    time.sleep(2)

    # 文章标签
    if 'tags' in front_matter and front_matter['tags']:
        tags = front_matter['tags']
    else:
        tags = csdn_config['tags']
    if tags:
        add_tag = driver.find_element(By.XPATH,
                                      '//div[@class="mark_selection"]//button[@class="tag__btn-tag" and contains(text(),"添加文章标签")]')
        add_tag.click()
        time.sleep(1)
        tag_input = driver.find_element(By.XPATH, '//div[@class="mark_selection_box"]//input[contains(@placeholder,"请输入文字搜索")]')
        for tag in tags:
            tag_input.send_keys(tag)
            time.sleep(2)
            tag_input.send_keys(Keys.ENTER)
            time.sleep(1)

        # 关闭按钮
        close_button = driver.find_element(By.XPATH, '//div[@class="mark_selection_box"]//button[@title="关闭"]')
        close_button.click()
        time.sleep(1)

    # 文章封面
    if 'image' in front_matter and front_matter['image']:
        file_input = driver.find_element(By.XPATH, "//input[@class='el-upload__input' and @type='file']")
        # 文件上传不支持远程文件上传，所以需要把图片下载到本地
        file_input.send_keys(download_image(front_matter['image']))
        time.sleep(2)

    # 摘要
    if 'description' in front_matter and front_matter['description']:
        summary = front_matter['description']
    else:
        summary = common_config['summary']
    if summary:
        summary_input = driver.find_element(By.XPATH, '//div[@class="desc-box"]//textarea[contains(@placeholder,"摘要：会在推荐、列表等场景外露")]')
        summary_input.send_keys(summary)
        time.sleep(2)

    # 分类专栏
    categories = csdn_config['categories']
    if categories:
        # 先点击新建分类专栏
        add_category = driver.find_element(By.XPATH, '//div[@id="tagList"]//button[@class="tag__btn-tag" and contains(text(),"新建分类专栏")]')
        add_category.click()
        time.sleep(1)
        for category in categories:
            category_input = driver.find_element(By.XPATH, f'//input[@type="checkbox" and @value="{category}"]/..')
            category_input.click()
            time.sleep(1)
        # 点击关闭按钮
        close_button = driver.find_element(By.XPATH, '//div[@class="tag__options-content"]//button[@class="modal__close-button button" and @title="关闭"]')
        close_button.click()
        time.sleep(1)

    # 可见范围
    visibility = csdn_config['visibility']
    if visibility:
        visibility_input = driver.find_element(By.XPATH,f'//div[@class="switch-box"]//label[contains(text(),"{visibility}")]')
        parent_element = visibility_input.find_element(By.XPATH, '..')
        parent_element.click()

    # 发布
    if auto_publish:
        publish_button = driver.find_element(By.XPATH, '//div[@class="modal__button-bar"]//button[contains(text(),"发布文章")]')
        publish_button.click()

def get_published_articles():
    """获取已发布文章列表"""
    common_config = read_common()
    try:
        return set(read_file_lines(common_config['published_record_file']))
    except:
        return set()

def mark_as_published(filename):
    """将文章标记为已发布"""
    common_config = read_common()
    with open(common_config['published_record_file'], 'a') as f:
        f.write(f"{filename}\tcsdn\t{time.strftime('%Y-%m-%d %H:%M:%S')}\n")

def save_last_published_file_name(filename):
    write_to_file(filename, last_published_file_name)

def publish_to_csdn(content=None):
    """发布到CSDN平台"""
    common_config = read_common()
    driver_type = common_config['driver_type']
    
    try:
        if driver_type == 'chrome':
            # 启动浏览器驱动服务
            service = selenium.webdriver.chrome.service.Service(common_config['service_location'])
            # Chrome 的调试地址
            debugger_address = common_config['debugger_address']
            # 创建Chrome选项，重用现有的浏览器实例
            options = selenium.webdriver.chrome.options.Options()
            options.page_load_strategy = 'normal'  # 设置页面加载策略为'normal' 默认值, 等待所有资源下载
            options.add_experimental_option('debuggerAddress', debugger_address)
            # 使用服务和选项初始化WebDriver
            driver = webdriver.Chrome(service=service, options=options)
        elif driver_type == 'firefox':
            # 启动浏览器驱动服务
            service = selenium.webdriver.firefox.service.Service(common_config['service_location'],
                                                                service_args=['--marionette-port', '2828',
                                                                            '--connect-existing'])
            # 创建firefox选项，重用现有的浏览器实例
            options = selenium.webdriver.firefox.options.Options()
            options.page_load_strategy = 'normal'  # 设置页面加载策略为'normal' 默认值, 等待所有资源下载
            driver = webdriver.Firefox(service=service, options=options)

        driver.implicitly_wait(10)  # 设置隐式等待时间为10秒
        
        csdn_publisher(driver, content)
        
        if content:
            mark_as_published(os.path.basename(content))
            save_last_published_file_name(os.path.basename(content))
            
    except Exception as e:
        print("CSDN publishing error:")
        traceback.print_exc()
        print(e)
    finally:
        # 在需要的时候关闭浏览器，不要关闭浏览器进程
        driver.quit()

"""
./chrome --remote-debugging-port=9222
"""

if __name__ == '__main__':
    common_config = read_common()
    content_dir = common_config['content_dir']
    
    print("选择你要发布到CSDN的博客,输入序号:")
    file_list = list_files(content_dir, ".md")
    published_articles = get_published_articles()
    
    # 过滤掉已发布的文章
    unpublished_files = []
    for file_name in file_list:
        base_name = os.path.basename(file_name)
        if base_name not in published_articles:
            unpublished_files.append(file_name)
    
    # 只显示未发布的文章
    for index, file_name in enumerate(unpublished_files):
        print(f"{index}: {os.path.basename(file_name)}")
        
    try:
        print("\n上次发布的博客是: " + read_head(last_published_file_name))
    except:
        print("\n没有上次发布记录")
        
    file_choice = input("\n请选择要发布的文章 (输入序号): ")
    print("")

    if len(unpublished_files) > int(file_choice) >= 0:
        file_path = unpublished_files[int(file_choice)]
        print("你要发布的文章是:", file_path)
        confirm = input("确认发布到CSDN? (y/n): ")
        if confirm.lower() == 'y':
            publish_to_csdn(file_path)
            print("发布完成!")
        else:
            print("已取消发布")
    else:
        print("无效的选择") 