import os
import shutil

import requests
import time

from dotenv import load_dotenv
from git import Repo, Actor

# 加载 .env 文件
load_dotenv()

# ---------------- 配置 ----------------
GITHUB_USERNAME_1 = os.getenv("GITHUB_USERNAME_1")  # 目标账号（获取成就）
GITHUB_USERNAME_2 = os.getenv("GITHUB_USERNAME_2")  # 工具账号

GITHUB_USER1_EMAIL = os.getenv("GITHUB_USER1_EMAIL")
GITHUB_USER2_EMAIL = os.getenv("GITHUB_USER2_EMAIL")

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
def sync_with_remote(local_repo):
    print("🔄 同步远程仓库最新代码...")
    origin = local_repo.remote("origin")
    origin.fetch()
    local_repo.git.checkout("main")
    local_repo.git.pull("origin", "main")

def create_branch(local_repo, branch_name):
    print(f"🌱 新建分支 {branch_name}")
    new_branch = local_repo.create_head(branch_name)
    new_branch.checkout()

def commit_with_coauthor(local_repo, branch_name, i):
    print("📝 提交 commit (带 co-author)...")
    file_name = "dummy.txt"
    file_path = os.path.join(local_repo.working_tree_dir, file_name)

    # 创建新文件
    with open(file_path, "a") as f:
        f.write(f"Update #{i} by {GITHUB_USERNAME_1} with {GITHUB_USERNAME_2}\n")

    index = local_repo.index
    index.add("*")

    author = Actor(GITHUB_USERNAME_1, GITHUB_USER1_EMAIL)
    committer = Actor(GITHUB_USERNAME_1, GITHUB_USER1_EMAIL)

    commit_msg = (
        f"Add update with co-author\n\n"
        f"Co-authored-by: {GITHUB_USERNAME_2} <{GITHUB_USER2_EMAIL}>"
    )
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

def merge_pr(pr_number):
    print(f"✅ 合并 PR #{pr_number}...")
    gh_request("PUT", f"/repos/{GITHUB_USERNAME_1}/{REPO_NAME}/pulls/{pr_number}/merge", PAT_1, json={"merge_method": "squash"})

def delete_branch(branch_name):
    print(f"🗑 删除分支 {branch_name}")
    gh_request("DELETE", f"/repos/{GITHUB_USERNAME_1}/{REPO_NAME}/git/refs/heads/{branch_name}", PAT_1)

# ---------------- 执行 48 次 ----------------
def main():
    # 克隆目标账号 fork 的仓库
    repo_url = f"https://{PAT_1}@github.com/{GITHUB_USERNAME_1}/{REPO_NAME}.git"
    repo_dir = f"./{REPO_NAME}"
    if not os.path.exists(repo_dir):
        local_repo = Repo.clone_from(repo_url, repo_dir)
    else:
        local_repo = Repo(repo_dir)

# Disclaimer: Be cautious when modifying the loop count here, as excessive operations may lead to account restrictions by GitHub.
# 免责声明：谨慎修改这里的循环此处次数，过多操作可能导致账号被 GitHub 限制

    for i in range(1, 5):
        sync_with_remote(local_repo)
        branch_name = f"feature-{i}"
        create_branch(local_repo, branch_name)
        commit_with_coauthor(local_repo, branch_name, i)
        pr = create_pr(branch_name)
        pr_number = pr["number"]
        time.sleep(2)
        merge_pr(pr_number)
        delete_branch(branch_name)
        time.sleep(3)

    shutil.rmtree(repo_dir)
    print("🎉 完成所有操作！")

if __name__ == "__main__":
    main()
