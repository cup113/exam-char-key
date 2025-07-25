/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = app.findCollectionByNameOrId("pbc_1676376271")

  // update collection data
  unmarshal({
    "createRule": "",
    "listRule": "",
    "updateRule": ""
  }, collection)

  return app.save(collection)
}, (app) => {
  const collection = app.findCollectionByNameOrId("pbc_1676376271")

  // update collection data
  unmarshal({
    "createRule": null,
    "listRule": null,
    "updateRule": null
  }, collection)

  return app.save(collection)
})
