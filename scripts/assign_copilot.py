#!/usr/bin/env python3
"""
Assign GitHub issues to the Copilot coding agent via GraphQL API.

Usage:
    python assign_copilot.py --repo owner/name --issue 123
"""

import os
import sys
import argparse
import requests

GITHUB_GRAPHQL = "https://api.github.com/graphql"


def get_copilot_actor_id(repo: str, token: str) -> str:
    """Get the copilot-swe-agent actor ID for a repository."""
    owner, name = repo.split("/")

    query = """
    query($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
        suggestedActors(capabilities: [CAN_BE_ASSIGNED], first: 20) {
          nodes {
            login
            id
          }
        }
      }
    }
    """

    response = requests.post(
        GITHUB_GRAPHQL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={"query": query, "variables": {"owner": owner, "name": name}}
    )

    data = response.json()

    if "errors" in data:
        raise RuntimeError(f"GraphQL errors: {data['errors']}")

    actors = data["data"]["repository"]["suggestedActors"]["nodes"]

    for actor in actors:
        if "copilot" in actor["login"].lower():
            return actor["id"]

    raise RuntimeError(
        "copilot-swe-agent not found in suggested actors. "
        "Ensure Copilot Coding Agent is enabled for this repository."
    )


def get_issue_node_id(repo: str, issue_number: int, token: str) -> str:
    """Get the node ID for an issue."""
    owner, name = repo.split("/")

    query = """
    query($owner: String!, $name: String!, $number: Int!) {
      repository(owner: $owner, name: $name) {
        issue(number: $number) {
          id
        }
      }
    }
    """

    response = requests.post(
        GITHUB_GRAPHQL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "query": query,
            "variables": {"owner": owner, "name": name, "number": issue_number}
        }
    )

    data = response.json()

    if "errors" in data:
        raise RuntimeError(f"GraphQL errors: {data['errors']}")

    return data["data"]["repository"]["issue"]["id"]


def assign_copilot(repo: str, issue_number: int, token: str) -> dict:
    """Assign an issue to the Copilot coding agent."""
    copilot_id = get_copilot_actor_id(repo, token)
    issue_id = get_issue_node_id(repo, issue_number, token)

    mutation = """
    mutation($issueId: ID!, $assigneeIds: [ID!]!) {
      addAssigneesToAssignable(input: {
        assignableId: $issueId,
        assigneeIds: $assigneeIds
      }) {
        assignable {
          ... on Issue {
            number
            title
            assignees(first: 5) {
              nodes {
                login
              }
            }
          }
        }
      }
    }
    """

    response = requests.post(
        GITHUB_GRAPHQL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "query": mutation,
            "variables": {"issueId": issue_id, "assigneeIds": [copilot_id]}
        }
    )

    result = response.json()

    if "errors" in result:
        raise RuntimeError(f"GraphQL errors: {result['errors']}")

    assignable = result["data"]["addAssigneesToAssignable"]["assignable"]
    assignees = [a["login"] for a in assignable["assignees"]["nodes"]]

    print(f"Issue #{issue_number} assigned to: {assignees}")

    return {
        "issue_number": assignable["number"],
        "title": assignable["title"],
        "assignees": assignees
    }


def main():
    parser = argparse.ArgumentParser(
        description="Assign a GitHub issue to Copilot coding agent"
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="Repository in owner/name format"
    )
    parser.add_argument(
        "--issue",
        required=True,
        type=int,
        help="Issue number to assign"
    )
    args = parser.parse_args()

    token = os.environ.get("GH_TOKEN")
    if not token:
        print("Error: GH_TOKEN environment variable not set", file=sys.stderr)
        sys.exit(1)

    try:
        result = assign_copilot(args.repo, args.issue, token)
        print(f"Successfully assigned issue #{result['issue_number']}: {result['title']}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
