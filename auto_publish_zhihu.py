import os
import selenium
from selenium import webdriver
from utils.yaml_file_utils import read_common, read_zhihu
from publisher.zhihu_publisher import zhihu_publisher
from utils.file_utils import list_files, read_file_lines
import time

def setup_driver():
    """Initialize and return the webdriver based on config"""
    common_config = read_common()
    driver_type = common_config['driver_type']
    
    if driver_type == 'chrome':
        service = selenium.webdriver.chrome.service.Service(common_config['service_location'])
        options = selenium.webdriver.chrome.options.Options()
        options.page_load_strategy = 'normal'
        options.add_experimental_option('debuggerAddress', common_config['debugger_address'])
        driver = webdriver.Chrome(service=service, options=options)
    elif driver_type == 'firefox':
        service = selenium.webdriver.firefox.service.Service(
            common_config['service_location'],
            service_args=['--marionette-port', '2828', '--connect-existing']
        )
        options = selenium.webdriver.firefox.options.Options()
        options.page_load_strategy = 'normal'
        driver = webdriver.Firefox(service=service, options=options)
    
    driver.implicitly_wait(10)
    return driver

def get_published_articles(published_record_file):
    """Get list of already published articles"""
    try:
        return set(read_file_lines(published_record_file))
    except:
        return set()

def mark_as_published(filename, published_record_file):
    """Mark article as published"""
    with open(published_record_file, 'a') as f:
        f.write(f"{filename}\tzhihu\t{time.strftime('%Y-%m-%d %H:%M:%S')}\n")

def auto_publish_zhihu(max_articles=None, publish_interval=60):
    """Main function to automatically publish articles to Zhihu
    
    Args:
        max_articles (int, optional): Maximum number of articles to publish. None means no limit.
        publish_interval (int, optional): Interval between publishing articles in seconds. Defaults to 60.
    """
    common_config = read_common()
    content_dir = common_config['content_dir']
    published_record_file = common_config['published_record_file']

    # Get list of markdown files
    file_list = list_files(content_dir, ".md")
    published_articles = get_published_articles(published_record_file)
    
    # Filter out already published articles
    unpublished_files = [
        file_name for file_name in file_list 
        if os.path.basename(file_name) not in published_articles
    ]

    if not unpublished_files:
        print("No unpublished articles found.")
        return

    # Limit the number of articles to publish if max_articles is specified
    if max_articles is not None:
        unpublished_files = unpublished_files[:max_articles]
        print(f"Will publish up to {max_articles} articles")

    # Initialize webdriver
    driver = setup_driver()

    try:
        # Publish each unpublished article
        for i, file_path in enumerate(unpublished_files):
            try:
                print(f"Publishing: {os.path.basename(file_path)}")
                zhihu_publisher(driver, file_path)
                mark_as_published(os.path.basename(file_path), published_record_file)
                print(f"Successfully published: {os.path.basename(file_path)}")
                
                # Add delay between articles, but not after the last one
                if i < len(unpublished_files) - 1:
                    print(f"Waiting {publish_interval} seconds before publishing next article...")
                    time.sleep(publish_interval)
            except Exception as e:
                print(f"Error publishing {os.path.basename(file_path)}: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    auto_publish_zhihu(max_articles=1)  # Example: Publish up to 3 articles with default 60s interval 