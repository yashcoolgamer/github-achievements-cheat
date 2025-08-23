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
GITHUB_USER1_EMAIL = os.getenv("GITHUB_USER1_EMAIL")

REPO_OWNER = os.getenv("REPO_OWNER")
REPO_NAME = os.getenv("REPO_NAME")

# PATs
PAT_1 = os.getenv("GITHUB_PAT_1")

BASE_API = "https://api.github.com"

# ---------------- 辅助函数 ----------------
def gh_request(method, url, token, **kwargs):
    headers = {"Authorization": f"token {token}"}
    r = requests.request(method, BASE_API + url, headers=headers, **kwargs)
    if r.status_code >= 300:
        raise Exception(f"GitHub API Error {r.status_code}: {r.text}")

    if r.status_code == 204 or not r.text.strip():
        return {}

    return r.json()

# ---------------- 主流程 ----------------
def create_branch(local_repo, branch_name):
    print(f"🌱 新建分支 {branch_name}")
    new_branch = local_repo.create_head(branch_name)
    new_branch.checkout()

def commit(local_repo, branch_name):
    print("📝 提交 commit...")
    file_name = "dummy.txt"
    file_path = os.path.join(local_repo.working_tree_dir, file_name)

    # 创建新文件
    with open(file_path, "a") as f:
        f.write(f"You Only live Once")

    index = local_repo.index
    index.add("*")

    author = Actor(GITHUB_USERNAME_1, GITHUB_USER1_EMAIL)
    committer = Actor(GITHUB_USERNAME_1, GITHUB_USER1_EMAIL)

    commit_msg = (f"update with yolo")
    index.commit(commit_msg, author=author, committer=committer)

    origin = local_repo.remote("origin")
    origin.push(refspec=f"{branch_name}:{branch_name}")

def create_pr(branch_name):
    print("📬 创建 PR...")
    data = {
        "title": f"Demo PR {branch_name}",
        "head": f"{GITHUB_USERNAME_1}:{branch_name}",
        "base": "main"
    }
    return gh_request("POST", f"/repos/{GITHUB_USERNAME_1}/{REPO_NAME}/pulls", PAT_1, json=data)

def close_pr(pr_number):
    print(f"🚫 关闭 PR #{pr_number}...")
    data = {
        "state": "closed"
    }
    return gh_request("PATCH", f"/repos/{GITHUB_USERNAME_1}/{REPO_NAME}/pulls/{pr_number}", PAT_1, json=data)

def delete_branch(branch_name):
    print(f"🗑 删除分支 {branch_name}")
    gh_request("DELETE", f"/repos/{GITHUB_USERNAME_1}/{REPO_NAME}/git/refs/heads/{branch_name}", PAT_1)

def main():
    # 克隆目标账号 fork 的仓库
    repo_url = f"https://{PAT_1}@github.com/{GITHUB_USERNAME_1}/{REPO_NAME}.git"
    repo_dir = f"./{REPO_NAME}"
    if not os.path.exists(repo_dir):
        local_repo = Repo.clone_from(repo_url, repo_dir)
    else:
        local_repo = Repo(repo_dir)

    create_branch(local_repo, "quick-draw")
    commit(local_repo, "quick-draw")
    pr = create_pr("quick-draw")
    pr_number = pr["number"]
    print(f"✅ 创建 PR #{pr_number}...")
    time.sleep(2)
    close_pr(pr_number)
    time.sleep(2)
    delete_branch("quick-draw")
    time.sleep(3)

    shutil.rmtree(repo_dir)
    print("🎉 完成所有操作！")

if __name__ == "__main__":
    main()