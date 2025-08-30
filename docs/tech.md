# 城市韌性模擬平台 - 技術文件（Tech Stack 與 Project Structure）

## 總覽

本架構採用完全前後端分離的模式。後端使用 Python FastAPI 提供高效能的 API 服務，負責所有核心運算；前端則使用 React.js 打造一個高互動性、資料驅動的視覺化使用者介面。

```null
urban-resilience-simulator/
├── backend/                  # Python FastAPI 後端專案 (維持不變)
│   ├── app/
│   │   ├── api/              # API 路由 (Endpoints)
│   │   │   ├── v1/           # API 版本 v1
│   │   │   │   ├── endpoints/
│   │   │   │   │   ├── world.py        # 處理世界生成的 API (POST /api/v1/world)
│   │   │   │   │   ├── simulation.py   # 處理模擬與分析的 API (POST /api/v1/simulation)
│   │   │   │   │   └── impact.py       # 處理衝擊分析的 API (POST /api/v1/impact)
│   │   │   │   └── __init__.py
│   │   ├── core/             # 核心商業邏輯 (PRD中的模組實作)
│   │   │   ├── config.py         # 應用程式設定
│   │   │   ├── world_synthesizer/  # 模組一：世界合成器
│   │   │   ├── simulation_engine/  # 模組二：模擬引擎
│   │   │   └── impact_analyzer/    # 模組三：衝擊分析模組
│   │   ├── schemas/          # Pydantic 資料驗證模型
│   │   │   ├── request.py        # API 請求的模型
│   │   │   └── response.py       # API 回應的模型
│   │   ├── __init__.py
│   │   └── main.py           # FastAPI 應用程式入口
│   ├── tests/                # 測試程式碼
│   ├── .env.example          # 環境變數範例
│   └── requirements.txt      # Python 依賴套件
│
├── frontend/                 # React.js 前端專案 (全新 React 架構)
│   ├── public/               # 公開靜態資源 (如 index.html, favicon.ico)
│   ├── src/
│   │   ├── api/              # 專門處理後端 API 請求的模組
│   │   │   └── apiClient.js    # 設定 Axios 或 Fetch 實例，集中管理 API Base URL 等
│   │   ├── assets/           # 靜態資源 (圖片, 全域 CSS)
│   │   ├── components/       # 可複用的、純粹的 UI 元件 ("Dumb Components")
│   │   │   ├── dashboard/
│   │   │   │   └── DashboardPanel.jsx # 整個儀表板面板
│   │   │   ├── controls/
│   │   │   │   └── ControlPanel.jsx  # 包含模擬按鈕、圖層選項的控制面板
│   │   │   └── ui/               # 通用基礎元件 (Button.jsx, Modal.jsx, Spinner.jsx)
│   │   ├── hooks/              # 自定義 React Hooks，用於封裝可複用的邏輯
│   │   │   └── useSimulation.js    # 核心 Hook，封裝與後端 API 互動、觸發模擬的邏輯
│   │   ├── services/           # 封裝非 React 的外部服務或複雜邏輯
│   │   │   └── mapService.js     # **關鍵：** 封裝所有與 Leaflet.js 互動的底層邏輯
│   │   ├── store/              # 全域狀態管理 (建議使用 Zustand 或 Redux Toolkit)
│   │   │   └── useSimulationStore.js # Zustand Store: 集中管理地圖數據、模擬結果、UI狀態
│   │   ├── containers/         # **容器元件** ("Smart Components")
│   │   │   └── MapContainer.jsx    # 負責整合 mapService 和 React 狀態，並渲染地圖
│   │   ├── pages/              # 頁面級元件
│   │   │   └── SimulationPage.jsx  # 組合所有元件，構成使用者看到的主要模擬頁面
│   │   ├── App.jsx             # 應用程式根元件，可在此處設定路由 (未來擴充用)
│   │   └── main.jsx            # React 應用程式的入口點
│   ├── .env.example
│   └── package.json            # 前端依賴套件 (react, react-dom, leaflet, zustand, axios)
│
├── docs/                     # 專案文件
│   ├── prd.md            # 我們的產品需求文件
│   └── tech.md           # 包含 Tech stack 和專案架構的文件
│
├── docker-compose.yml        # Docker 容器化配置，方便一鍵啟動開發環境
└── README.md                 # 專案說明文件


```



### React 前端架構重點解析：

1. **元件職責劃分 (`components` vs. `containers` vs. `pages`):**

   - `components/`: 存放**純 UI 元件**，它們只負責根據傳入的 props 顯示介面，自身不包含複雜的業務邏輯。例如，一個 `Button` 元件。

   - `containers/`: 存放**容器元件**，它們是「聰明」的，負責處理數據和邏輯，並將其傳遞給純 UI 元件。`MapContainer.jsx` 就是一個絕佳例子，它會處理所有與地圖相關的狀態和副作用，但地圖本身的渲染可能還是由 `mapService` 處理。

   - `pages/`: 負責**組合**多個元件和容器，構建成一個完整的頁面。`SimulationPage.jsx` 會將 `MapContainer`、`DashboardPanel` 和 `ControlPanel` 組合在一起。

2. **邏輯與狀態分離 (`hooks`, `services`, `store`):**

   - `services/mapService.js`: 這是**非常重要的設計模式**。我們將所有 Leaflet 的實例化、圖層添加/移除等直接操作 DOM 的程式碼全部封裝在這裡。React 元件只會呼叫這個 service 提供的簡單方法（如 `mapService.addTrees(treesData)`），而**不需要在 React 元件內部直接接觸 Leaflet**，這讓程式碼更乾淨、更容易測試。

   - `store/useSimulationStore.js`: 使用 **Zustand** (一個輕量級的狀態管理庫) 來存放需要跨元件共享的全域狀態，例如後端回傳的世界地圖資料、模擬後的分析結果、目前哪個圖層是可見的等等。這避免了複雜的 props-drilling (層層傳遞屬性)。

   - `hooks/useSimulation.js`: 自定義 Hook 是 React 的精髓。這個 Hook 可以將「發送 API 請求 -> 更新 Store 狀態 -> 處理載入中/錯誤狀態」的整套流程封裝起來，讓頁面元件的程式碼極其簡潔。

3. **API 抽象層 (`api/apiClient.js`):**

   - 在此檔案中設定好 API 的基礎 URL、請求標頭 (headers)、攔截器 (interceptors) 等。所有元件都從這裡發送請求，而不是在各自內部寫死 URL。這樣未來如果 API 路徑變更，只需要修改一個地方。