"""Lightweight static checks; does not require an AWS account or EKS cluster."""

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def load(relative_path):
    file_path = ROOT / relative_path
    return yaml.safe_load(file_path.read_text(encoding="utf-8"))


def main():
    dep = load("k8s/base/deployment.yaml")
    svc = load("k8s/base/service.yaml")
    base = load("k8s/base/kustomization.yaml")
    overlay = load("k8s/overlays/dev/kustomization.yaml")
    argocd = load("argocd/application-dev.yaml")
    public = load("k8s/optional/public-nlb-service.yaml")

    assert dep["kind"] == "Deployment"
    assert dep["spec"]["replicas"] == 2, "Two application pods are expected"
    pod_labels = dep["spec"]["template"]["metadata"]["labels"]
    assert svc["spec"]["selector"] == pod_labels, "Service selector must match Pods"
    assert set(base["resources"]) == {"deployment.yaml", "service.yaml"}
    assert overlay["resources"] == ["../../base"]
    assert overlay["namespace"] == "gitops-demo"
    assert len(overlay["images"]) == 1
    assert overlay["images"][0]["name"] == "gitops-flask"
    assert argocd["spec"]["source"]["path"] == "k8s/overlays/dev"
    assert argocd["spec"]["source"]["repoURL"].endswith("/aws-eks-argocd-gitops.git")
    assert argocd["spec"]["destination"]["namespace"] == "gitops-demo"
    assert "automated" not in argocd["spec"]["syncPolicy"], "First sync must be manual"
    assert public["spec"]["loadBalancerClass"] == "service.k8s.aws/nlb"
    assert public["spec"]["selector"] == pod_labels
    print("PASS: valid YAML, two replicas, matching selectors, correct GitOps paths")


if __name__ == "__main__":
    main()
