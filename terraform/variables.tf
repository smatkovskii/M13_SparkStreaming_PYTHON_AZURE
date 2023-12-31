variable "ENV" {
  type = string
  description = "The prefix which should be used for all resources in this environment."
}

variable "LOCATION" {
  type = string
  description = "The Azure Region in which all resources in this example should be created."
}

variable "BDCC_REGION" {
  type = string
  description = "The BDCC Region for billing."
  default = "global"
}

variable "STORAGE_ACCOUNT_REPLICATION_TYPE" {
  type = string
  description = "Storage Account replication type."
  default = "LRS"
}
