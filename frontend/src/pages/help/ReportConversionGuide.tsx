import React from 'react';
import { Link } from 'react-router-dom';

const ReportConversionGuide: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      <nav className="text-sm text-fluent-deepOcean-300 mb-6">
        <Link to="/" className="hover:text-fluent-gold-500">首页</Link>
        <span className="mx-2">›</span>
        <Link to="/help" className="hover:text-fluent-gold-500">帮助中心</Link>
        <span className="mx-2">›</span>
        <span className="text-fluent-deepOcean-500">报告格式转换指南</span>
      </nav>

      <div className="acrylic rounded-2xl shadow-fluent-lg p-8 border border-white/30 mb-8">
        <h1 className="text-3xl font-bold text-fluent-deepOcean-500 mb-4">
          📄 报告格式转换指南
        </h1>
        <p className="text-lg text-fluent-deepOcean-300 mb-6">
          房都督平台生成的报告为Markdown格式，您可以通过以下方法将其转换为PDF、Word或Excel格式。
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="bg-fluent-gold-50 rounded-xl p-4 text-center">
            <span className="text-3xl">🖨️</span>
            <h3 className="font-semibold text-fluent-deepOcean-500 mt-2">浏览器打印</h3>
            <p className="text-sm text-fluent-deepOcean-300">最简单，无需安装</p>
          </div>
          <div className="bg-fluent-deepOcean-50 rounded-xl p-4 text-center">
            <span className="text-3xl">💻</span>
            <h3 className="font-semibold text-fluent-deepOcean-500 mt-2">专用软件</h3>
            <p className="text-sm text-fluent-deepOcean-300">功能强大，支持批量</p>
          </div>
          <div className="bg-purple-50 rounded-xl p-4 text-center">
            <span className="text-3xl">⌨️</span>
            <h3 className="font-semibold text-fluent-deepOcean-500 mt-2">命令行工具</h3>
            <p className="text-sm text-fluent-deepOcean-300">自动化，可集成</p>
          </div>
        </div>
      </div>

      <div className="space-y-8">
        <section className="acrylic rounded-2xl shadow-fluent-md p-6 border border-white/30">
          <h2 className="text-xl font-semibold text-fluent-deepOcean-500 mb-4 flex items-center gap-2">
            <span className="w-8 h-8 rounded-full bg-fluent-gold-500 text-white flex items-center justify-center text-sm">1</span>
            浏览器打印转PDF（最简单）
          </h2>
          
          <div className="bg-fluent-deepOcean-50 rounded-xl p-4 mb-4">
            <p className="text-fluent-deepOcean-400 mb-3">
              这是最简单的方法，无需安装任何软件，直接使用浏览器的打印功能即可。
            </p>
            
            <ol className="list-decimal list-inside space-y-2 text-fluent-deepOcean-500">
              <li>在报告页面点击"下载HTML"按钮</li>
              <li>在浏览器中打开下载的HTML文件</li>
              <li>按 <kbd className="px-2 py-1 bg-fluent-deepOcean-200 rounded text-sm">Ctrl + P</kbd>（Mac用户按 <kbd className="px-2 py-1 bg-fluent-deepOcean-200 rounded text-sm">Cmd + P</kbd>）</li>
              <li>在打印对话框中选择"另存为PDF"</li>
              <li>点击"保存"即可</li>
            </ol>
          </div>
          
          <div className="bg-fluent-gold-50 rounded-xl p-4">
            <p className="text-sm text-fluent-gold-700">
              💡 提示：报告已预设打印样式，打印时会自动优化排版。建议使用Chrome或Edge浏览器获得最佳效果。
            </p>
          </div>
        </section>

        <section className="acrylic rounded-2xl shadow-fluent-md p-6 border border-white/30">
          <h2 className="text-xl font-semibold text-fluent-deepOcean-500 mb-4 flex items-center gap-2">
            <span className="w-8 h-8 rounded-full bg-fluent-gold-500 text-white flex items-center justify-center text-sm">2</span>
            使用Typora（推荐）
          </h2>
          
          <div className="bg-fluent-deepOcean-50 rounded-xl p-4 mb-4">
            <p className="text-fluent-deepOcean-400 mb-3">
              Typora是一款优雅的Markdown编辑器，支持直接导出PDF、Word、HTML等格式。
            </p>
            
            <h4 className="font-medium text-fluent-deepOcean-500 mb-2">安装Typora：</h4>
            <a href="https://typora.io/" target="_blank" className="text-fluent-gold-500 hover:text-fluent-gold-600 text-sm mb-4 inline-block">
              访问 typora.io 下载 →
            </a>
            
            <h4 className="font-medium text-fluent-deepOcean-500 mb-2 mt-4">使用步骤：</h4>
            <ol className="list-decimal list-inside space-y-2 text-fluent-deepOcean-500">
              <li>用Typora打开下载的.md文件</li>
              <li>点击菜单 "文件" → "导出"</li>
              <li>选择需要的格式（PDF/Word/HTML）</li>
              <li>保存文件即可</li>
            </ol>
          </div>
        </section>

        <section className="acrylic rounded-2xl shadow-fluent-md p-6 border border-white/30">
          <h2 className="text-xl font-semibold text-fluent-deepOcean-500 mb-4 flex items-center gap-2">
            <span className="w-8 h-8 rounded-full bg-fluent-gold-500 text-white flex items-center justify-center text-sm">3</span>
            使用Pandoc（命令行工具）
          </h2>
          
          <div className="bg-fluent-deepOcean-50 rounded-xl p-4 mb-4">
            <p className="text-fluent-deepOcean-400 mb-3">
              Pandoc是强大的文档转换工具，支持几乎所有文档格式之间的转换。
            </p>
            
            <h4 className="font-medium text-fluent-deepOcean-500 mb-2">安装Pandoc：</h4>
            <div className="bg-fluent-deepOcean-100 rounded-lg p-3 font-mono text-sm mb-4">
              <p className="text-fluent-deepOcean-500"># Windows (使用Chocolatey)</p>
              <p className="text-fluent-jade-600">choco install pandoc</p>
              <p className="text-fluent-deepOcean-500 mt-2"># macOS (使用Homebrew)</p>
              <p className="text-fluent-jade-600">brew install pandoc</p>
              <p className="text-fluent-deepOcean-500 mt-2"># Linux (Ubuntu/Debian)</p>
              <p className="text-fluent-jade-600">sudo apt-get install pandoc</p>
            </div>

            <h4 className="font-medium text-fluent-deepOcean-500 mb-2">常用转换命令：</h4>
            <div className="bg-fluent-deepOcean-100 rounded-lg p-3 font-mono text-sm space-y-2">
              <div>
                <p className="text-fluent-deepOcean-400"># 转换为PDF</p>
                <p className="text-fluent-jade-600">pandoc 报告.md -o 报告.pdf --pdf-engine=xelatex</p>
              </div>
              <div>
                <p className="text-fluent-deepOcean-400"># 转换为Word</p>
                <p className="text-fluent-jade-600">pandoc 报告.md -o 报告.docx</p>
              </div>
              <div>
                <p className="text-fluent-deepOcean-400"># 转换为HTML（带样式）</p>
                <p className="text-fluent-jade-600">pandoc 报告.md -o 报告.html -c report.css --standalone</p>
              </div>
              <div>
                <p className="text-fluent-deepOcean-400"># 批量转换（PowerShell）</p>
                <p className="text-fluent-jade-600">Get-ChildItem *.md | ForEach-Object {'{'}"pandoc $_.Name -o `"$($_.BaseName).pdf`"{'}'}</p>
              </div>
            </div>
          </div>
        </section>

        <section className="acrylic rounded-2xl shadow-fluent-md p-6 border border-white/30">
          <h2 className="text-xl font-semibold text-fluent-deepOcean-500 mb-4 flex items-center gap-2">
            <span className="w-8 h-8 rounded-full bg-fluent-gold-500 text-white flex items-center justify-center text-sm">4</span>
            在线转换工具
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-fluent-deepOcean-50 rounded-xl p-4">
              <h4 className="font-medium text-fluent-deepOcean-500 mb-2">CloudConvert</h4>
              <p className="text-sm text-fluent-deepOcean-400 mb-2">支持MD转PDF/Word/Excel等多种格式</p>
              <a href="https://cloudconvert.com" target="_blank" className="text-fluent-gold-500 hover:text-fluent-gold-600 text-sm">
                访问 cloudconvert.com →
              </a>
            </div>
            <div className="bg-fluent-deepOcean-50 rounded-xl p-4">
              <h4 className="font-medium text-fluent-deepOcean-500 mb-2">Convertio</h4>
              <p className="text-sm text-fluent-deepOcean-400 mb-2">简单易用的在线文件转换器</p>
              <a href="https://convertio.co" target="_blank" className="text-fluent-gold-500 hover:text-fluent-gold-600 text-sm">
                访问 convertio.co →
              </a>
            </div>
          </div>
        </section>

        <section className="acrylic rounded-2xl shadow-fluent-md p-6 border border-white/30">
          <h2 className="text-xl font-semibold text-fluent-deepOcean-500 mb-4 flex items-center gap-2">
            <span>❓</span>
            常见问题
          </h2>
          
          <div className="space-y-4">
            <div className="bg-fluent-deepOcean-50 rounded-xl p-4">
              <h4 className="font-medium text-fluent-deepOcean-500 mb-2">Q: 如何保留报告的样式？</h4>
              <p className="text-sm text-fluent-deepOcean-400">
                A: 下载"全套文件（ZIP）"，解压后CSS文件与MD文件放在同一目录。使用Typora或Pandoc时指定CSS文件即可保留样式。
              </p>
            </div>
            <div className="bg-fluent-deepOcean-50 rounded-xl p-4">
              <h4 className="font-medium text-fluent-deepOcean-500 mb-2">Q: 表格在PDF中显示不正确怎么办？</h4>
              <p className="text-sm text-fluent-deepOcean-400">
                A: 建议使用Typora导出，它对Markdown表格支持最好。或者使用Pandoc并添加 --pdf-engine=xelatex 参数。
              </p>
            </div>
            <div className="bg-fluent-deepOcean-50 rounded-xl p-4">
              <h4 className="font-medium text-fluent-deepOcean-500 mb-2">Q: 如何批量转换多个报告？</h4>
              <p className="text-sm text-fluent-deepOcean-400">
                A: 使用Pandoc的批量转换命令，或使用Typora的批量导出功能（需要高级版）。
              </p>
            </div>
            <div className="bg-fluent-deepOcean-50 rounded-xl p-4">
              <h4 className="font-medium text-fluent-deepOcean-500 mb-2">Q: CSV文件如何打开？</h4>
              <p className="text-sm text-fluent-deepOcean-400">
                A: CSV文件可以用Excel、Google Sheets或任何文本编辑器打开。双击CSV文件通常会自动用Excel打开。
              </p>
            </div>
          </div>
        </section>
      </div>

      <div className="mt-8 text-center">
        <Link
          to="/dashboard"
          className="inline-block bg-gradient-to-r from-fluent-gold-400 to-fluent-gold-600 text-fluent-deepOcean-500 px-8 py-3 rounded-xl font-medium hover:shadow-gold-glow transition-all duration-300"
        >
          返回仪表盘
        </Link>
      </div>
    </div>
  );
};

export default ReportConversionGuide;
