/* =========================================
ASSET CATEGORY SERVICE
=========================================

Maneja todas las operaciones relacionadas
con Asset Categories.

========================================= */

import api from "./apis"

/* =========================================
GET ALL CATEGORIES
========================================= */

export const getAssetCategories = async () => {

const response = await api.get("/asset-categories/")

return response.data

}

/* =========================================
CREATE CATEGORY
========================================= */

export const createAssetCategory = async (data) => {

const response = await api.post(

"/asset-categories/",

data

)

return response.data

}

/* =========================================
UPDATE CATEGORY
========================================= */

export const updateAssetCategory = async (id,data) => {

const response = await api.put(

`/asset-categories/${id}`,

data

)

return response.data

}

/* =========================================
DELETE CATEGORY
========================================= */

export const deleteAssetCategory = async (id) => {

const response = await api.delete(

`/asset-categories/${id}`

)

return response.data

}