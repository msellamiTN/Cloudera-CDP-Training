from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from .hbase_client import HBaseUnavailable, ProductAnalyticsRepository

app = FastAPI(
    title="DataCo Product Analytics API",
    version="1.0.0",
    description="Read product analytics records from HBase through Thrift.",
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "dataco-api"}


@app.get("/products/{product_id}/analytics")
def product_analytics(product_id: str):
    repository = ProductAnalyticsRepository()
    try:
        product = repository.get_product(product_id)
        if product is None:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
        return product
    except HBaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    finally:
        repository.close()


@app.get("/")
def root():
    return JSONResponse({"message": "DataCo API. Open /docs for the API contract."})
