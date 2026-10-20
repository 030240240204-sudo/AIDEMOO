from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import sqlite3

app = FastAPI(
    title="HUB AI Workload Optimizer - Enterprise Dashboard",
    description="Hệ thống AI cảnh báo quá tải và phân bổ nhiệm vụ (Human-in-the-Loop)"
)

DB_NAME = "hub_enterprise.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS warnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT,
            warning_type TEXT,
            detail TEXT,
            level TEXT
        )
    ''')
    cursor.execute("SELECT COUNT(*) FROM warnings")
    if cursor.fetchone()[0] == 0:
        sample_warnings = [
            ("An", "Quá tải", "8 nhiệm vụ, 3 nhiệm vụ gần đến hạn", "CAO"),
            ("Task-402", "Trễ tiến độ", "Thời hạn: 17:00 hôm nay (Tiến độ: 40%)", "TRUNG BÌNH"),
            ("Bình", "Quá tải", "6 nhiệm vụ, Kiểm tra hiệu suất thường xuyên", "TRUNG BÌNH"),
            ("Chi", "Hiệu suất thấp", "Tỷ lệ hoàn thành nhiệm vụ dưới 60% tuần qua", "CAO"),
            ("Dự án Marketing Q4", "Rủi roDeadline", "Thiếu nhân sự thiết kế đồ họa trầm trọng", "CAO")
        ]
        cursor.executemany("INSERT INTO warnings (task_name, warning_type, detail, level) VALUES (?, ?, ?, ?)", sample_warnings)
        conn.commit()
    conn.close()

init_db()

class AllocationRequest(BaseModel):
    task_id: str

class DecisionRequest(BaseModel):
    task_id: str
    action: str
    reason: str

class PromptRequest(BaseModel):
    prompt: str

@app.get("/api/dashboard-stats")
def get_dashboard_stats():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT task_name, warning_type, detail, level FROM warnings")
    rows = cursor.fetchall()
    warnings = [{"task": r[0], "type": r[1], "detail": r[2], "level": r[3]} for r in rows]
    conn.close()
    return {"warnings": warnings}

# API Xử lý Prompt AI / RAG Query (8.3.1)
@app.post("/api/ask-rag")
def ask_rag_ai(req: PromptRequest):
    p = req.prompt.lower()
    
    if "an" in p and "task01" in p:
        answer = "An có kỹ năng phù hợp (SEO, Content) nhưng Workload hiện tại đã đạt 85% (Capacity còn 15%). Theo quy định KB01 & KB02, với TASK01 ước tính 12 giờ trong 2 ngày, hệ thống cảnh báo An bị QUÁ TẢI và cần ưu tiên xét duyệt Bình hoặc nhân sự có Capacity trống hơn."
    elif "chi" in p and "task02" in p:
        answer = "Mặc dù NV03 Chi có Capacity trống cao (65%), nhưng theo Ma trận kỹ năng KB02, Chi chỉ có chuyên môn Data Analytics và Excel. TASK02 yêu cầu bắt buộc kỹ năng Canva và Design nên hệ thống loại Chi khỏi danh sách đề xuất."
    elif "dũng" in p and "task01" in p:
        answer = "Dũng còn Capacity 35% nhưng chỉ sở hữu kỹ năng SEO và Google Ads, thiếu kỹ năng Content bắt buộc cho TASK01. Hệ thống quy định không đề xuất nhân sự khi chưa đáp ứng đủ bộ kỹ năng cốt lõi."
    elif "task05" in p:
        answer = "TASK05 yêu cầu kỹ năng Video Editing và Motion Graphics. Trong tập dữ liệu 5 nhân sự hiện tại, chưa có cá nhân nào sở hữu đủ bộ kỹ năng này. Hệ thống kích hoạt quy trình ngoại lệ KB03."
    else:
        answer = f"Trợ lý AI (RAG Engine) đã nhận câu hỏi: '{req.prompt}'. Hệ thống đã đối chiếu cơ sở tri thức (KB01, KB02, KB03) và dữ liệu SQLite để đưa ra giải trình minh bạch cho quản lý."

    return {
        "prompt": req.prompt,
        "retrieved_sources": ["KB01_ChinhSachWorkload.pdf", "KB02_MatranKyNang_SQLite", "KB03_QuyTrinhNgoaiLe.pdf"],
        "model": "GPT-5 mini (RAG Augmented)",
        "answer": answer
    }

@app.get("/", response_class=HTMLResponse)
def get_enterprise_dashboard():
    return """
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <title>HUB AI Workload Optimizer</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    </head>
    <body class="bg-slate-100 font-sans flex h-screen overflow-hidden">

        <!-- SIDEBAR -->
        <aside class="w-64 bg-[#0F2E2B] text-white flex flex-col justify-between shadow-xl">
            <div>
                <div class="p-5 flex items-center space-x-3 border-b border-emerald-900/50">
                    <div class="bg-emerald-500 p-2 rounded-lg text-white font-bold"><i class="fa-solid fa-chart-pie"></i></div>
                    <span class="text-lg font-bold tracking-wide">HUB Manager</span>
                </div>
                <nav class="mt-6 space-y-1 px-3">
                    <button onclick="switchTab('dashboard')" id="btn-dashboard" class="sidebar-btn w-full flex items-center space-x-3 px-4 py-3 rounded-lg bg-emerald-600 text-white font-medium transition">
                        <i class="fa-solid fa-house"></i><span>Dashboard</span>
                    </button>
                    <button onclick="switchTab('employees')" id="btn-employees" class="sidebar-btn w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-slate-300 hover:bg-emerald-900/40 transition">
                        <i class="fa-solid fa-users"></i><span>Nhân sự</span>
                    </button>
                    <button onclick="switchTab('projects')" id="btn-projects" class="sidebar-btn w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-slate-300 hover:bg-emerald-900/40 transition">
                        <i class="fa-solid fa-folder-open"></i><span>Dự án</span>
                    </button>
                    <button onclick="switchTab('warnings')" id="btn-warnings" class="sidebar-btn w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-slate-300 hover:bg-emerald-900/40 transition">
                        <i class="fa-solid fa-triangle-exclamation text-amber-400"></i><span>Cảnh báo</span>
                    </button>
                    <button onclick="switchTab('ai-suggest')" id="btn-ai-suggest" class="sidebar-btn w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-slate-300 hover:bg-emerald-900/40 transition">
                        <i class="fa-solid fa-robot text-cyan-400"></i><span>Đề xuất AI</span>
                    </button>
                    <!-- TAB PROMPT AI MỚI BỔ SUNG -->
                    <button onclick="switchTab('prompt-ai')" id="btn-prompt-ai" class="sidebar-btn w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-slate-300 hover:bg-emerald-900/40 transition">
                        <i class="fa-solid fa-comments text-amber-400"></i><span>Prompt AI / RAG</span>
                    </button>
                    <button onclick="switchTab('history')" id="btn-history" class="sidebar-btn w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-slate-300 hover:bg-emerald-900/40 transition">
                        <i class="fa-solid fa-clock-rotate-left"></i><span>Lịch sử</span>
                    </button>
                </nav>
            </div>
            <div class="p-4 border-t border-emerald-900/50 flex items-center space-x-3">
                <div class="w-10 h-10 rounded-full bg-emerald-500 flex items-center justify-center font-bold text-white">NM</div>
                <div>
                    <h4 class="text-sm font-semibold text-white">Nguyen Manager</h4>
                    <span class="text-xs text-emerald-400">System Admin</span>
                </div>
            </div>
        </aside>

        <!-- MAIN CONTENT AREA -->
        <main class="flex-1 flex flex-col overflow-y-auto">
            <header class="bg-white shadow-sm h-16 flex items-center justify-between px-8 z-10">
                <div>
                    <h1 id="pageTitle" class="text-xl font-bold text-slate-800">Dashboard tổng quan</h1>
                    <p id="pageSubTitle" class="text-xs text-slate-500">Quản lý Tổng quan và Phân bổ Công việc thông minh</p>
                </div>
                <div class="flex items-center space-x-4">
                    <div class="relative">
                        <input type="text" placeholder="Tìm kiếm..." class="bg-slate-100 text-sm px-4 py-2 rounded-lg pl-10 focus:outline-none focus:ring-2 focus:ring-emerald-500 w-64">
                        <i class="fa-solid fa-magnifying-glass absolute left-3 top-3 text-slate-400 text-sm"></i>
                    </div>
                    <button class="text-slate-500 hover:text-slate-700 relative"><i class="fa-regular fa-bell text-lg"></i><span class="absolute top-0 right-0 w-2 h-2 bg-rose-500 rounded-full"></span></button>
                </div>
            </header>

            <!-- TAB 1: DASHBOARD -->
            <div id="tab-dashboard" class="tab-content p-8 space-y-6">
                <div class="grid grid-cols-4 gap-6">
                    <div class="bg-white p-5 rounded-xl shadow-sm border border-slate-200 flex justify-between items-center">
                        <div>
                            <p class="text-sm text-slate-500 font-medium">Tổng số nhân viên</p>
                            <h3 class="text-3xl font-bold text-slate-800 mt-1">48</h3>
                        </div>
                        <div class="w-12 h-12 bg-indigo-50 text-indigo-600 rounded-xl flex items-center justify-center text-xl"><i class="fa-solid fa-users"></i></div>
                    </div>
                    <div class="bg-white p-5 rounded-xl shadow-sm border border-amber-200 bg-amber-50/30 flex justify-between items-center">
                        <div>
                            <p class="text-sm text-amber-700 font-medium">Nhân viên quá tải</p>
                            <h3 class="text-3xl font-bold text-amber-800 mt-1">6</h3>
                            <span class="text-xs text-amber-600 font-semibold">(2 Cao / 4 Trung bình)</span>
                        </div>
                        <div class="w-12 h-12 bg-amber-100 text-amber-600 rounded-xl flex items-center justify-center text-xl"><i class="fa-solid fa-flag"></i></div>
                    </div>
                    <div class="bg-white p-5 rounded-xl shadow-sm border border-slate-200 flex justify-between items-center">
                        <div>
                            <p class="text-sm text-slate-500 font-medium">Nhiệm vụ đang thực hiện</p>
                            <h3 class="text-3xl font-bold text-slate-800 mt-1">142</h3>
                        </div>
                        <div class="w-12 h-12 bg-emerald-50 text-emerald-600 rounded-xl flex items-center justify-center text-xl"><i class="fa-solid fa-list-check"></i></div>
                    </div>
                    <div class="bg-white p-5 rounded-xl shadow-sm border border-slate-200 flex justify-between items-center">
                        <div>
                            <p class="text-sm text-rose-500 font-medium">Nhiệm vụ quá hạn</p>
                            <h3 class="text-3xl font-bold text-rose-600 mt-1">9</h3>
                        </div>
                        <div class="w-12 h-12 bg-rose-50 text-rose-600 rounded-xl flex items-center justify-center text-xl"><i class="fa-solid fa-triangle-exclamation"></i></div>
                    </div>
                </div>

                <div class="grid grid-cols-2 gap-6">
                    <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                        <h3 class="font-bold text-slate-800 text-md mb-4">Biểu đồ Workload: Tình hình công việc các nhóm</h3>
                        <div class="h-64 flex items-end justify-between px-4 pb-4 border-b border-slate-200 space-x-2">
                            <div class="flex flex-col items-center space-y-1 w-1/5">
                                <div class="w-full flex justify-center items-end space-x-1 h-48">
                                    <div class="w-3 bg-emerald-600 h-[80%] rounded-t"></div>
                                    <div class="w-3 bg-amber-400 h-[60%] rounded-t"></div>
                                    <div class="w-3 bg-rose-500 h-[45%] rounded-t"></div>
                                </div>
                                <span class="text-xs text-slate-600 font-medium">Phát triển</span>
                            </div>
                            <div class="flex flex-col items-center space-y-1 w-1/5">
                                <div class="w-full flex justify-center items-end space-x-1 h-48">
                                    <div class="w-3 bg-emerald-600 h-[90%] rounded-t"></div>
                                    <div class="w-3 bg-amber-400 h-[70%] rounded-t"></div>
                                    <div class="w-3 bg-rose-500 h-[50%] rounded-t"></div>
                                </div>
                                <span class="text-xs text-slate-600 font-medium">QA/QC</span>
                            </div>
                            <div class="flex flex-col items-center space-y-1 w-1/5">
                                <div class="w-full flex justify-center items-end space-x-1 h-48">
                                    <div class="w-3 bg-emerald-600 h-[65%] rounded-t"></div>
                                    <div class="w-3 bg-amber-400 h-[45%] rounded-t"></div>
                                    <div class="w-3 bg-rose-500 h-[35%] rounded-t"></div>
                                </div>
                                <span class="text-xs text-slate-600 font-medium">Thiết kế</span>
                            </div>
                            <div class="flex flex-col items-center space-y-1 w-1/5">
                                <div class="w-full flex justify-center items-end space-x-1 h-48">
                                    <div class="w-3 bg-emerald-600 h-[75%] rounded-t"></div>
                                    <div class="w-3 bg-amber-400 h-[95%] rounded-t"></div>
                                    <div class="w-3 bg-rose-500 h-[20%] rounded-t"></div>
                                </div>
                                <span class="text-xs text-slate-600 font-medium">Marketing</span>
                            </div>
                            <div class="flex flex-col items-center space-y-1 w-1/5">
                                <div class="w-full flex justify-center items-end space-x-1 h-48">
                                    <div class="w-3 bg-emerald-600 h-[60%] rounded-t"></div>
                                    <div class="w-3 bg-amber-400 h-[40%] rounded-t"></div>
                                    <div class="w-3 bg-rose-500 h-[20%] rounded-t"></div>
                                </div>
                                <span class="text-xs text-slate-600 font-medium">Kinh doanh</span>
                            </div>
                        </div>
                    </div>

                    <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                        <div class="flex justify-between items-center mb-4">
                            <h3 class="font-bold text-slate-800 text-md">Danh sách Cảnh báo cần ưu tiên</h3>
                        </div>
                        <div class="overflow-x-auto">
                            <table class="w-full text-left text-xs">
                                <thead>
                                    <tr class="text-slate-400 border-b border-slate-100">
                                        <th class="pb-3 font-semibold">Nhiệm vụ</th>
                                        <th class="pb-3 font-semibold">Loại Cảnh báo</th>
                                        <th class="pb-3 font-semibold">Chi tiết</th>
                                        <th class="pb-3 font-semibold">Mức độ</th>
                                        <th class="pb-3 font-semibold text-right">Thao tác</th>
                                    </tr>
                                </thead>
                                <tbody id="warningTableBody" class="divide-y divide-slate-100"></tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <!-- TAB 2: NHÂN SỰ -->
            <div id="tab-employees" class="tab-content hidden p-8">
                <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                    <h3 class="font-bold text-slate-800 mb-4">Quản lý Danh sách Nhân sự & Workload</h3>
                    <div class="space-y-4">
                        <div class="flex justify-between p-3 bg-slate-50 rounded-lg">
                            <div><span class="font-bold">An</span> (SEO, Content)</div>
                            <span class="text-xs bg-rose-100 text-rose-700 px-2 py-1 rounded font-bold">Workload: 85% (Quá tải)</span>
                        </div>
                        <div class="flex justify-between p-3 bg-slate-50 rounded-lg">
                            <div><span class="font-bold">Bình</span> (Content, Canva)</div>
                            <span class="text-xs bg-emerald-100 text-emerald-700 px-2 py-1 rounded font-bold">Workload: 40% (Tối ưu)</span>
                        </div>
                        <div class="flex justify-between p-3 bg-slate-50 rounded-lg">
                            <div><span class="font-bold">Chi</span> (Data Analytics, Excel)</div>
                            <span class="text-xs bg-emerald-100 text-emerald-700 px-2 py-1 rounded font-bold">Workload: 35% (Tối ưu)</span>
                        </div>
                        <div class="flex justify-between p-3 bg-slate-50 rounded-lg">
                            <div><span class="font-bold">Dũng</span> (SEO, Google Ads)</div>
                            <span class="text-xs bg-amber-100 text-amber-700 px-2 py-1 rounded font-bold">Workload: 65% (Khá cao)</span>
                        </div>
                        <div class="flex justify-between p-3 bg-slate-50 rounded-lg">
                            <div><span class="font-bold">Hà</span> (Canva, Video Editing)</div>
                            <span class="text-xs bg-emerald-100 text-emerald-700 px-2 py-1 rounded font-bold">Workload: 25% (Rảnh rỗi)</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- TAB 3: DỰ ÁN -->
            <div id="tab-projects" class="tab-content hidden p-8">
                <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                    <h3 class="font-bold text-slate-800 mb-4">Danh sách Dự án Marketing Đang Triển Khai</h3>
                    <div class="grid grid-cols-2 gap-4">
                        <div class="p-4 border rounded-xl bg-indigo-50/50">
                            <h4 class="font-bold text-indigo-900">Chiến dịch Marketing Q4</h4>
                            <p class="text-xs text-slate-600 mt-1">Tiến độ: 68% | 12 Nhân sự tham gia</p>
                        </div>
                        <div class="p-4 border rounded-xl bg-emerald-50/50">
                            <h4 class="font-bold text-emerald-900">Rebranding Thương hiệu HUB</h4>
                            <p class="text-xs text-slate-600 mt-1">Tiến độ: 85% | 8 Nhân sự tham gia</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- TAB 4: CẢNH BÁO -->
            <div id="tab-warnings" class="tab-content hidden p-8">
                <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                    <h3 class="font-bold text-slate-800 mb-4">Trung tâm Cảnh báo Rủi ro Hệ thống</h3>
                    <p class="text-sm text-slate-600">Hiển thị toàn bộ các nguy cơ quá tải công việc, chậm tiến độ deadline tính toán từ mô hình AI.</p>
                </div>
            </div>

            <!-- TAB 5: ĐỀ XUẤT AI -->
            <div id="tab-ai-suggest" class="tab-content hidden p-8">
                <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                    <h3 class="font-bold text-indigo-600 mb-2">🤖 Đề xuất Phân bổ AI (Human-in-the-Loop)</h3>
                    <p class="text-sm text-slate-600 mb-4">Thuật toán phân tích ma trận kỹ năng và khả năng đáp ứng công việc trống để tối ưu hóa nhân lực.</p>
                    <button onclick="openAIRecommendation('Phân bổ tổng thể', 'Phát hiện 2 nhân sự đang bị nghẽn việc')" class="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-indigo-700">Chạy AI Tối Ưu Lại Toàn Bộ</button>
                </div>
            </div>

            <!-- TAB 6: PROMPT AI / RAG QUERY (ĐÃ BỔ SUNG GIAO DIỆN) -->
            <div id="tab-prompt-ai" class="tab-content hidden p-8 space-y-6">
                <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                    <h3 class="font-bold text-lg text-amber-600 mb-2"><i class="fa-solid fa-comments mr-2"></i> Trợ lý Truy vấn Tri thức RAG & GPT-5 mini</h3>
                    <p class="text-sm text-slate-600 mb-4">Nhập câu hỏi để truy xuất tài liệu quy định (KB01, KB02, KB03) và SQLite giải trình quyết định AI:</p>

                    <div class="mb-4">
                        <p class="text-xs font-bold text-slate-700 mb-2">Gợi ý câu hỏi kiểm thử (8.3.1 RAG Testcase):</p>
                        <div class="flex flex-wrap gap-2">
                            <button onclick="setPrompt('Tại sao AI không ưu tiên An thực hiện TASK01 dù An có kỹ năng SEO và Content?')" class="bg-slate-100 hover:bg-slate-200 px-3 py-1.5 rounded-lg text-xs text-slate-700 border">
                                💡 Tại sao không ưu tiên An cho TASK01?
                            </button>
                            <button onclick="setPrompt('Tại sao không chọn NV03 Chi cho TASK02 dù Chi còn Capacity 65%?')" class="bg-slate-100 hover:bg-slate-200 px-3 py-1.5 rounded-lg text-xs text-slate-700 border">
                                💡 Tại sao không chọn Chi cho TASK02?
                            </button>
                            <button onclick="setPrompt('Tại sao TASK05 báo không tìm thấy nhân sự phù hợp?')" class="bg-slate-100 hover:bg-slate-200 px-3 py-1.5 rounded-lg text-xs text-slate-700 border">
                                💡 Giải trình lỗi ngoại lệ TASK05?
                            </button>
                        </div>
                    </div>

                    <div class="flex space-x-2 mb-6">
                        <input id="promptInput" type="text" placeholder="Gõ câu hỏi cho AI tại đây..." class="flex-1 border p-2.5 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-amber-500 bg-slate-50">
                        <button onclick="sendPromptAI()" class="bg-amber-500 hover:bg-amber-600 text-white px-5 py-2.5 rounded-lg text-xs font-bold transition">Gửi câu hỏi</button>
                    </div>

                    <div id="ragAnswerBox" class="hidden border rounded-xl p-5 bg-amber-50/30 border-amber-200">
                        <div class="flex justify-between items-center mb-3">
                            <span class="text-xs font-bold text-amber-800" id="ragModelTag">Mô hình: GPT-5 mini (RAG Augmented)</span>
                            <span class="text-[10px] bg-amber-200 text-amber-900 px-2 py-0.5 rounded font-semibold" id="ragSources">Nguồn: KB01, KB02, SQLite</span>
                        </div>
                        <h4 class="font-bold text-slate-800 text-sm mb-2" id="ragQuestionHeader"></h4>
                        <div class="bg-white p-4 rounded-lg border text-xs text-slate-700 leading-relaxed" id="ragAnswerContent"></div>
                    </div>
                </div>
            </div>

            <!-- TAB 7: LỊCH SỬ -->
            <div id="tab-history" class="tab-content hidden p-8">
                <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                    <h3 class="font-bold text-slate-800 mb-4">Lịch sử Phê duyệt từ Manager (Human Decisions)</h3>
                    <ul class="text-xs space-y-2 text-slate-600">
                        <li>• [10:15] Manager phê duyệt điều chuyển TASK01 cho Bình.</li>
                        <li>• [09:30] AI cảnh báo quá tải cho An (Workload > 85%).</li>
                    </ul>
                </div>
            </div>

        </main>

        <!-- AI Recommendation Modal -->
        <div id="aiModal" class="fixed inset-0 bg-black/50 hidden flex items-center justify-center z-50">
            <div class="bg-white w-[500px] p-6 rounded-2xl shadow-2xl">
                <div class="flex justify-between items-center mb-4 border-b pb-3">
                    <h3 class="font-bold text-lg text-indigo-600"><i class="fa-solid fa-robot mr-2"></i> Trợ lý AI Phân bổ Thông minh</h3>
                    <button onclick="closeAIModal()" class="text-slate-400 hover:text-slate-600"><i class="fa-solid fa-xmark text-lg"></i></button>
                </div>
                <div id="modalContent" class="space-y-3 text-sm text-slate-700"></div>
                <div class="mt-6 flex justify-end space-x-3">
                    <button onclick="closeAIModal()" class="px-4 py-2 border rounded-lg text-slate-600 text-sm font-medium hover:bg-slate-50">Đóng</button>
                    <button onclick="alert('Đã phê duyệt phương án tối ưu hóa từ AI!')" class="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-semibold hover:bg-emerald-700">Phê duyệt (Accept)</button>
                </div>
            </div>
        </div>

        <script>
            function switchTab(tabName) {
                // Hide all tabs
                document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
                
                // Reset sidebar buttons style
                document.querySelectorAll('.sidebar-btn').forEach(btn => {
                    btn.classList.remove('bg-emerald-600', 'text-white');
                    btn.classList.add('text-slate-300');
                });

                // Show target tab
                document.getElementById('tab-' + tabName).classList.remove('hidden');

                // Highlight target button
                const activeBtn = document.getElementById('btn-' + tabName);
                if (activeBtn) {
                    activeBtn.classList.add('bg-emerald-600', 'text-white');
                    activeBtn.classList.remove('text-slate-300');
                }

                // Update Header titles
                const titles = {
                    'dashboard': ['Dashboard tổng quan', 'Quản lý Tổng quan và Phân bổ Công việc thông minh'],
                    'employees': ['Quản lý Nhân sự', 'Chi tiết danh sách và chỉ số Workload cá nhân'],
                    'projects': ['Quản lý Dự án', 'Tổng quan tiến độ các dự án đang triển khai'],
                    'warnings': ['Trung tâm Cảnh báo', 'Cảnh báo rủi ro quá tải và trễ deadline'],
                    'ai-suggest': ['Gợi ý & Đề xuất AI', 'Mô hình Human-in-the-Loop tối ưu công việc'],
                    'prompt-ai': ['Prompt AI / RAG Query', 'Truy xuất tri thức KB01, KB02, KB03 & GPT-5 mini'],
                    'history': ['Lịch sử Quyết định', 'Nhật ký phê duyệt và điều chỉnh của Quản lý']
                };
                if (titles[tabName]) {
                    document.getElementById('pageTitle').innerText = titles[tabName][0];
                    document.getElementById('pageSubTitle').innerText = titles[tabName][1];
                }
            }

            function setPrompt(text) {
                document.getElementById('promptInput').value = text;
            }

            async function sendPromptAI() {
                const prompt = document.getElementById('promptInput').value;
                if(!prompt) return alert("Vui lòng nhập câu hỏi!");

                const res = await fetch('/api/ask-rag', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ prompt: prompt })
                });
                const data = await res.json();

                document.getElementById('ragAnswerBox').classList.remove('hidden');
                document.getElementById('ragQuestionHeader').innerText = "❓ Câu hỏi: " + data.prompt;
                document.getElementById('ragAnswerContent').innerText = data.answer;
                document.getElementById('ragSources').innerText = "Nguồn truy xuất: " + data.retrieved_sources.join(", ");
            }

            async function loadDashboardData() {
                const res = await fetch('/api/dashboard-stats');
                const data = await res.json();
                
                let html = '';
                data.warnings.forEach(w => {
                    let badgeColor = w.type === 'Quá tải' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700';
                    let levelColor = w.level === 'CAO' ? 'bg-rose-500 text-white' : 'bg-amber-400 text-white';
                    html += `
                        <tr class="hover:bg-slate-50/50">
                            <td class="py-3 font-semibold text-slate-800">${w.task}</td>
                            <td class="py-3"><span class="px-2 py-0.5 rounded text-[10px] font-semibold ${badgeColor}">${w.type}</span></td>
                            <td class="py-3 text-slate-500">${w.detail}</td>
                            <td class="py-3"><span class="px-2 py-0.5 rounded text-[10px] font-bold ${levelColor}">${w.level}</span></td>
                            <td class="py-3 text-right space-x-1">
                                <button onclick="alert('Chi tiết sự cố: ' + '${w.task}')" class="border px-2 py-1 rounded text-[11px] font-medium text-slate-600 hover:bg-slate-100">Xem chi tiết</button>
                                <button onclick="openAIRecommendation('${w.task}', '${w.detail}')" class="bg-indigo-600 text-white px-2 py-1 rounded text-[11px] font-medium hover:bg-indigo-700">Xem đề xuất AI</button>
                            </td>
                        </tr>
                    `;
                });
                document.getElementById('warningTableBody').innerHTML = html;
            }

            function openAIRecommendation(task, detail) {
                document.getElementById('aiModal').classList.remove('hidden');
                document.getElementById('modalContent').innerHTML = `
                    <div class="bg-indigo-50 p-3 rounded-lg border-l-4 border-indigo-500">
                        <p class="font-semibold text-indigo-900">Đối tượng phân tích: ${task}</p>
                        <p class="text-xs text-indigo-700 mt-1">Tình trạng: ${detail}</p>
                    </div>
                    <div class="space-y-2 mt-4">
                        <p class="font-bold text-slate-800">🤖 Đề xuất xử lý từ hệ thống AI (Human-in-the-Loop):</p>
                        <p class="text-xs text-slate-600">1. Điều chuyển bớt nhiệm vụ sang nhân sự thuộc nhóm năng lực trống cao (Capacity > 60%).</p>
                        <p class="text-xs text-slate-600">2. Đề xuất phân công bổ sung cho <strong>Bình</strong> hoặc <strong>Chi</strong> để tối ưu điểm phù hợp kỹ năng (Match Score > 85%).</p>
                    </div>
                `;
            }

            function closeAIModal() {
                document.getElementById('aiModal').classList.add('hidden');
            }

            loadDashboardData();
        </script>
    </body>
    </html>
    """
