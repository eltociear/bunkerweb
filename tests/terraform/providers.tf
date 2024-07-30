terraform {  
  required_providers {
    scaleway = {
      source = "scaleway/scaleway"
      version = "2.42.1"
    }
    kubectl = {
      source = "gavinbunney/kubectl"
      version = "1.14.0"
    }
    kubernetes = {
      source = "hashicorp/kubernetes"
      version = "2.31.0"
    }
  }
}