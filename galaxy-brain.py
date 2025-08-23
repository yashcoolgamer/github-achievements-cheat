import os
import shutil
import time

import requests
from dotenv import load_dotenv
from git import Repo, Actor

# 加载环境变量
load_dotenv()

# ---------------- 配置 ----------------
GITHUB_USERNAME_1 = os.getenv("GITHUB_USERNAME_1")  # 目标账号（获取成就）
GITHUB_USERNAME_2 = os.getenv("GITHUB_USERNAME_2")  # 工具账号

GITHUB_USER1_EMAIL = os.getenv("GITHUB_USER1_EMAIL")
GITHUB_USER2_EMAIL = os.getenv("GITHUB_USER2_EMAIL")

REPO_OWNER = os.getenv("REPO_OWNER")
REPO_NAME = os.getenv("REPO_NAME")

PAT_1 = os.getenv("GITHUB_PAT_1")
PAT_2 = os.getenv("GITHUB_PAT_2")
# ---------------- 主流程 ----------------
def create_qa_discussion(title, body):
    url = "https://api.github.com/graphql"

    # 第一步：获取仓库ID和现有分类
    query_repo = """
    query {
      repository(owner: "%s", name: "%s") {
        id
        discussionCategories(first: 10) {
          nodes {
            id
            name
            isAnswerable
          }
        }
      }
    }
    """ % (REPO_OWNER, REPO_NAME)

    headers = {
        "Authorization": f"Bearer {PAT_2}",  # 工具账号
        "Content-Type": "application/json"
    }

    response = requests.post(url, json={"query": query_repo}, headers=headers)
    if response.status_code != 200:
        raise Exception(f"GitHub API Error {response.status_code}: {response.text}")

    data = response.json()
    if "errors" in data:
        raise Exception(f"GraphQL Error: {data['errors']}")

    repository_id = data["data"]["repository"]["id"]
    categories = data["data"]["repository"]["discussionCategories"]["nodes"]

    print("仓库中的讨论分类:")
    for cat in categories:
        print(f"- {cat['name']} (isAnswerable={cat['isAnswerable']})")
    # FIXME
    # 查找已有的 Q&A 分类
    qa_category_id = None
    for category in categories:
        if category["isAnswerable"]:
            qa_category_id = category["id"]
            print(f"找到 Q&A 分类: {category['name']}")
            break

    # 如果没有 Q&A 分类，抛出清晰的错误信息
    if not qa_category_id:
        raise Exception(
            "No Q&A discussion category found in the repository. "
            f"Please create a Q&A category in the repository settings at: "
            f"https://github.com/{REPO_OWNER}/{REPO_NAME}/settings/discussion_categories"
        )

    # 第二步：创建 discussion
    mutation = """
    mutation($input: CreateDiscussionInput!) {
      createDiscussion(input: $input) {
        discussion {
          id
          url
        }
      }
    }
    """
    variables = {
        "input": {
            "repositoryId": repository_id,
            "categoryId": qa_category_id,
            "body": body,
            "title": title
        }
    }

    response = requests.post(url, json={"query": mutation, "variables": variables}, headers=headers)
    if response.status_code != 200:
        raise Exception(f"GitHub API Error {response.status_code}: {response.text}")

    data = response.json()
    if "errors" in data:
        raise Exception(f"GraphQL Error: {data['errors']}")

    discussion = data["data"]["createDiscussion"]["discussion"]
    print(f"✅ ({GITHUB_USERNAME_2}) 成功创建 Q&A 讨论: {title}")
    return discussion

def answer_qa_discussion(discussion_url):
    # 从URL中提取discussionNumber
    parts = discussion_url.split("/")
    discussion_number = parts[-1]

    # GitHub GraphQL API 端点
    url = "https://api.github.com/graphql"

    # 第一步：获取discussion ID
    query_discussion = """
    query {
      repository(owner: "%s", name: "%s") {
        discussion(number: %s) {
          id
        }
      }
    }
    """ % (REPO_OWNER, REPO_NAME, discussion_number)

    headers = {
        "Authorization": f"Bearer {PAT_1}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json={"query": query_discussion}, headers=headers)

    if response.status_code != 200:
        raise Exception(f"GitHub API Error {response.status_code}: {response.text}")

    data = response.json()
    if "errors" in data:
        raise Exception(f"GraphQL Error: {data['errors']}")

    discussion_id = data["data"]["repository"]["discussion"]["id"]

    # 第二步：添加回答
    mutation = """
    mutation {
      addDiscussionComment(input: {
        discussionId: "%s",
        body: "这是我的回答。我认为解决方案是..."
      }) {
        comment {
          id
          url
        }
      }
    }
    """ % (discussion_id)

    response = requests.post(url, json={"query": mutation}, headers=headers)

    if response.status_code != 200:
        raise Exception(f"GitHub API Error {response.status_code}: {response.text}")

    data = response.json()
    if "errors" in data:
        raise Exception(f"GraphQL Error: {data['errors']}")

    comment = data["data"]["addDiscussionComment"]["comment"]
    print(f"✅ ({GITHUB_USERNAME_1})成功回答了问题")

    # 第三步：将回答标记为答案
    mutation = """
    mutation {
      markDiscussionCommentAsAnswer(input: {
        commentId: "%s"
      }) {
        discussion {
          id
        }
      }
    }
    """ % (comment["id"])

    headers = {
        "Authorization": f"Bearer {PAT_2}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json={"query": mutation}, headers=headers)

    if response.status_code != 200:
        raise Exception(f"GitHub API Error {response.status_code}: {response.text}")

    print(f"✅ ({GITHUB_USERNAME_2})成功将回答标记为最佳答案")

    return comment

def main():
    # 克隆目标账号 fork 的仓库
    repo_url = f"https://{PAT_1}@github.com/{GITHUB_USERNAME_1}/{REPO_NAME}.git"
    repo_dir = f"./{REPO_NAME}"
    if not os.path.exists(repo_dir):
        local_repo = Repo.clone_from(repo_url, repo_dir)
    else:
        local_repo = Repo(repo_dir)

    # 创建问题讨论
    discussion = create_qa_discussion(
        "这是一个问题标题",
        "这里是问题的详细描述，可以包含代码示例或其他内容。"
    )
    print(f"创建的讨论URL: {discussion['url']}")
    time.sleep(2)

    # 回答问题并标记为答案
    answer_qa_discussion(discussion['url'])
    time.sleep(2)

    shutil.rmtree(repo_dir)
    print("🎉 完成所有操作！")

if __name__ == "__main__":
    main()