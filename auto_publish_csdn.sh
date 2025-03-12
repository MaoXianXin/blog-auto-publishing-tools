#!/bin/bash

# ./auto_publish_csdn.sh 5  # 发布5篇文章

# 检查参数
if [ $# -ne 1 ]; then
    echo "Usage: $0 <number_of_articles>"
    exit 1
fi

num_articles=$1

# 检查输入是否为正整数
if ! [[ "$num_articles" =~ ^[0-9]+$ ]]; then
    echo "Please enter a valid positive number"
    exit 1
fi

# 循环发布文章
for ((i=1; i<=$num_articles; i++))
do
    echo "Publishing article $i of $num_articles..."
    # 自动选择第一篇未发布的文章 (输入0) 并自动确认 (输入y)
    (echo "0"; echo "y") | python3 publish_to_csdn.py
    
    # 等待一段时间再发布下一篇，避免触发反爬虫机制
    if [ $i -lt $num_articles ]; then
        echo "Waiting 60 seconds before publishing next article..."
        sleep 60
    fi
done

echo "All done! Published $num_articles articles."