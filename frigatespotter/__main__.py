# SPDX-License-Identifier: Apache-2.0
import uvicorn


if __name__ == "__main__":
    uvicorn.run("frigatespotter.app:app", host="0.0.0.0", port=8080)
