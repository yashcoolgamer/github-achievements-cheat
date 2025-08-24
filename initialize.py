import os

import requests
from dotenv import load_dotenv, set_key

# 加载 .env 文件
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
# ----------------------------------------

# 1️⃣ 获取当前用户名的函数（通过 GitHub API）
def get_github_username():
    headers = {
        "Authorization": f"token {PAT_1}",
        "Accept": "application/vnd.github.v3+json"
    }

    url = "https://api.github.com/user"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        username = response.json()['login']
        set_key('.env', 'GITHUB_USERNAME_1', username)
        return username
    else:
        raise Exception(f"无法获取用户名：{response.status_code} - {response.json().get('message')}")


# 2️⃣ Star 仓库
def star_a_repo(owner, repo_name):
    headers = {
        "Authorization": f"token {PAT_1}",
        "Accept": "application/vnd.github.v3+json"
    }

    url = f"https://api.github.com/user/starred/{owner}/{repo_name}"
    response = requests.put(url, headers=headers)

    if response.status_code == 204:
        print(f"✅ 已成功 star {owner}/{repo_name}")
    else:
        raise Exception(f"❌ Star 操作失败：{response.status_code} - {response.text}")


# 3️⃣ Fork 仓库
def fork_repo(owner, repo_name):
    headers = {
        "Authorization": f"token {PAT_1}",
        "Accept": "application/vnd.github.v3+json"
    }

    url = f"https://api.github.com/repos/{owner}/{repo_name}/forks"
    response = requests.post(url, headers=headers)

    if response.status_code == 202:
        print(f"✔️ 仓库 {owner}/{repo_name} fork 成功")
    else:
        raise Exception(f"❌ fork 操作失败：{response.status_code} - {response.text}")

# 4️⃣ 开启 discussions 功能
def enable_discussions(owner, repo_name):
    headers = {
        "Authorization": f"bearer {PAT_1}",
        "Content-Type": "application/json"
    }

    # 使用 GraphQL API 启用 Discussions
    graphql_url = "https://api.github.com/graphql"

    # 首先获取仓库ID
    query_repo_id = """
    query($owner:String!, $name:String!) {
      repository(owner:$owner, name:$name) {
        id
      }
    }
    """

    variables = {
        "owner": GITHUB_USERNAME_1,
        "name": REPO_NAME
    }

    response = requests.post(graphql_url, headers=headers, json={"query": query_repo_id, "variables": variables})

    if response.status_code != 200:
        raise Exception(f"❌ 获取仓库信息失败：{response.status_code} - {response.text}")

    repo_data = response.json().get("data", {}).get("repository", {})
    if not repo_data:
        raise Exception(f"❌ 找不到仓库信息：{response.text}")

    repo_id = repo_data.get("id")
    if not repo_id:
        raise Exception(f"❌ 找不到仓库ID：{response.text}")

    # 然后启用discussions
    enable_mutation = """
    mutation($repositoryId:ID!) {
      updateRepository(input:{repositoryId:$repositoryId, hasDiscussionsEnabled:true}) {
        repository {
          hasDiscussionsEnabled
        }
      }
    }
    """

    variables = {
        "repositoryId": repo_id
    }

    response = requests.post(graphql_url, headers=headers, json={"query": enable_mutation, "variables": variables})

    if response.status_code == 200 and not response.json().get("errors"):
        print(f"✅ 已成功为 {owner}/{repo_name} 开启 discussions 功能")
    else:
        error_message = response.json().get("errors", [{}])[0].get("message", response.text)
        raise Exception(f"❌ 开启 discussions 功能失败：{response.status_code} - {error_message}")

    categories = repo_data.get("discussionCategories", {}).get("nodes", [])
    print(f"ℹ️ 当前仓库的讨论分类: {[c['name'] for c in categories]}")

# 5️⃣ 添加工具账号为协作者
def add_collaborator(owner, repo_name, collaborator):
    token = os.getenv("GITHUB_PAT_1")
    if not token:
        raise ValueError("GITHUB_PAT_1 未在 .env 中设置")

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    url = f"https://api.github.com/repos/{owner}/{repo_name}/collaborators/{collaborator}"
    data = {
        "permission": "admin"
    }

    response = requests.put(url, headers=headers, json=data)

    if response.status_code == 201:
        print(f"✅ 已成功向 {collaborator} 发送协作邀请")
        return True
    elif response.status_code == 204:
        print(f"✅ {collaborator} 已经是协作者")
        return True
    else:
        raise Exception(f"❌ 发送协作邀请失败：{response.status_code} - {response.text}")


# 6️⃣ 接受协作邀请
def accept_invitation(collaborator_pat):
    token = collaborator_pat
    if not token:
        raise ValueError("协作者的 PAT 未提供")

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    # 首先获取所有邀请
    invites_url = "https://api.github.com/user/repository_invitations"
    response = requests.get(invites_url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"❌ 获取邀请列表失败：{response.status_code} - {response.text}")

    invitations = response.json()

    if not invitations:
        print("⚠️ 没有待处理的邀请")
        return

    # 接受所有邀请
    for invite in invitations:
        invite_id = invite["id"]
        repo_name = invite["repository"]["full_name"]

        accept_url = f"https://api.github.com/user/repository_invitations/{invite_id}"
        accept_response = requests.patch(accept_url, headers=headers)

        if accept_response.status_code == 204:
            print(f"✅ 已成功接受 {repo_name} 的协作邀请")
        else:
            print(f"❌ 接受邀请失败：{accept_response.status_code} - {accept_response.text}")

# 🔍 主程序入口
if __name__ == "__main__":
    REPO_OWNER = os.getenv("REPO_OWNER")
    REPO_NAME = os.getenv("REPO_NAME")

    try:
        # 获取用户名（即当前认证用户）
        username = get_github_username()
        print(f"👨‍💻 当前 GitHub 用户名：{username}")

        # # Star 仓库
        # star_a_repo(REPO_OWNER, REPO_NAME)

        # Fork 仓库
        fork_repo(REPO_OWNER, REPO_NAME)

        # 开启 discussions 功能
        enable_discussions(GITHUB_USERNAME_1, REPO_NAME)

        # 添加协作者
        collaborator = os.getenv("GITHUB_USERNAME_2")
        add_collaborator(username, REPO_NAME, collaborator)

        # 接受邀请
        collaborator_pat = os.getenv("GITHUB_PAT_2")
        accept_invitation(collaborator_pat)

    except Exception as e:
        print(f"发生了错误: {e}")
