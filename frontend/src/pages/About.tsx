import React from 'react'

const About: React.FC = () => {
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8 text-center">关于房都督AI</h1>
      
      {/* 产品愿景 */}
      <section className="bg-white rounded-lg shadow-md p-8 mb-12 border border-gray-200">
        <h2 className="text-2xl font-medium mb-6">产品愿景</h2>
        <p className="text-gray-700 leading-relaxed mb-6">
          房都督AI的产品愿景是成为房产领域可信赖的决策智能伙伴，通过技术手段消除信息特权，让每一次重大的房产决策都建立在充分、透明、可验证的信息基石之上。我们的价值主张不仅在于提供答案，更在于重塑获取答案的过程与信任关系。
        </p>
        
        <div className="mt-8">
          <h3 className="text-xl font-medium mb-4">从工具到可信伙伴的三层演进</h3>
          <div className="space-y-6">
            <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
              <h4 className="text-lg font-medium mb-2">1. 重构体验层</h4>
              <p className="text-gray-700 mb-3">
                将房产调研从一项枯燥、专业、充满不确定性的"体力+脑力劳动"，重构为一次清晰、可信、甚至有参与感的 "智能协作旅程"。
              </p>
              <p className="text-gray-600 italic">
                长期目标：让"先让房都督AI调研一下"成为房产决策的标准前置动作，定义新一代用户习惯。
              </p>
            </div>
            
            <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
              <h4 className="text-lg font-medium mb-2">2. 建立标准层</h4>
              <p className="text-gray-700 mb-3">
                通过提供可追溯、可验证的报告，在行业内建立 "透明调研" 的事实标准。推动房产信息服务从"营销话术"走向"数据证据"。
              </p>
              <p className="text-gray-600 italic">
                长期目标：成为房产信息质量与可信度的基准参考，其报告被用户、中介甚至金融机构广泛认可与引用。
              </p>
            </div>
            
            <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
              <h4 className="text-lg font-medium mb-2">3. 赋能生态层</h4>
              <p className="text-gray-700 mb-3">
                将核心的"多智能体调研引擎"开放为基础设施，赋能中介提升专业效率，赋能金融机构进行风险定价，赋能研究机构深化市场洞察。
              </p>
              <p className="text-gray-600 italic">
                长期目标：构建一个以透明、可信数据为核心的房产科技生态，成为生态中的关键能力提供商。
              </p>
            </div>
          </div>
        </div>
      </section>
      
      {/* 核心价值主张 */}
      <section className="bg-white rounded-lg shadow-md p-8 mb-12 border border-gray-200">
        <h2 className="text-2xl font-medium mb-6">核心价值主张</h2>
        <p className="text-gray-700 leading-relaxed mb-6">
          我们不是在做"更好的信息聚合"，而是在创造"新的决策服务品类"。其价值可通过与传统模式的直接对比来凸显。
        </p>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  价值维度
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  传统模式（房产平台/中介）
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  房都督AI模式
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  为用户创造的核心价值
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  信息呈现
                </td>
                <td className="px-6 py-4 whitespace-normal text-sm text-gray-500">
                  单向输出：经过美化或筛选的碎片化信息列表。
                </td>
                <td className="px-6 py-4 whitespace-normal text-sm text-gray-500">
                  双向可验：结构化的深度报告，且每个结论可点击溯源。
                </td>
                <td className="px-6 py-4 whitespace-normal text-sm text-gray-500">
                  掌控感与安心：从被动接收信息到主动验证信息，获得确定性。
                </td>
              </tr>
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  服务过程
                </td>
                <td className="px-6 py-4 whitespace-normal text-sm text-gray-500">
                  黑盒操作：用户不知道结论如何得出，数据从何而来。
                </td>
                <td className="px-6 py-4 whitespace-normal text-sm text-gray-500">
                  白盒剧场：全流程可视化，AI的"思考"与"行动"实时可见。
                </td>
                <td className="px-6 py-4 whitespace-normal text-sm text-gray-500">
                  信任与理解：透明度构建信任，过程展示本身具有教育价值，提升用户认知。
                </td>
              </tr>
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  核心能力
                </td>
                <td className="px-6 py-4 whitespace-normal text-sm text-gray-500">
                  连接与推荐：核心是匹配房源与客户。
                </td>
                <td className="px-6 py-4 whitespace-normal text-sm text-gray-500">
                  分析与研判：核心是提供跨维度、基于数据的独立分析。
                </td>
                <td className="px-6 py-4 whitespace-normal text-sm text-gray-500">
                  专业赋能：将普通用户武装成具备专业分析能力的决策者，弥合信息与认知鸿沟。
                </td>
              </tr>
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  利益立场
                </td>
                <td className="px-6 py-4 whitespace-normal text-sm text-gray-500">
                  向卖家收费：本质是销售渠道，与买家存在潜在利益冲突。
                </td>
                <td className="px-6 py-4 whitespace-normal text-sm text-gray-500">
                  向买家收费：是纯粹的"买方顾问"，立场与用户完全一致。
                </td>
                <td className="px-6 py-4 whitespace-normal text-sm text-gray-500">
                  同盟关系：用户确信服务提供者的目标是帮助自己做出更好决策，而非促成交易。
                </td>
              </tr>
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  交付成果
                </td>
                <td className="px-6 py-4 whitespace-normal text-sm text-gray-500">
                  销售机会与房源清单。
                </td>
                <td className="px-6 py-4 whitespace-normal text-sm text-gray-500">
                  决策依据与知识资产：一份可存档、可复用的深度调研报告与过程记录。
                </td>
                <td className="px-6 py-4 whitespace-normal text-sm text-gray-500">
                  长期价值：获得的不仅是当前决策支持，更是可沉淀的房产认知与方法论。
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
      
      {/* 核心市场驱动力 */}
      <section className="bg-white rounded-lg shadow-md p-8 mb-12 border border-gray-200">
        <h2 className="text-2xl font-medium mb-6">核心市场驱动力</h2>
        <div className="space-y-6">
          <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
            <h4 className="text-lg font-medium mb-2">1. 政策导向：呼唤透明与理性</h4>
            <p className="text-gray-700 mb-3">
              "房住不炒" 定调下，监管持续鼓励市场信息透明化，打击虚假宣传。多地推行 "二手房指导价" 、 "信息公开平台" 等政策。
            </p>
            <p className="text-primary font-medium">
              对房都督AI的利好：政策环境引导买卖双方更加依赖客观、中立的数据分析，而非炒作性信息。房都督AI的"可溯源"特性高度契合监管倡导的透明精神。
            </p>
          </div>
          
          <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
            <h4 className="text-lg font-medium mb-2">2. 技术成熟：AI智能体进入应用爆发前夜</h4>
            <p className="text-gray-700 mb-3">
              2023年以来，AI智能体（Agent） 框架（如LangChain、AutoGPT）成熟度快速提升，让复杂任务自动化从实验室走向应用。大语言模型（LLM）的推理与生成能力已可处理专业文本。
            </p>
            <p className="text-primary font-medium">
              对房都督AI的利好：使得构建低成本、高效率的"多AI协作调研团队"在技术上可行。云计算成本持续下降，使得实时计算与流媒体传输的可负担性大增。
            </p>
          </div>
          
          <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
            <h4 className="text-lg font-medium mb-2">3. 用户代际变迁：数字原住民成为决策主力</h4>
            <p className="text-gray-700 mb-3">
              85后、90后 正成为购房中坚力量，占比已超60%（基于多家房产机构报告估算）。他们习惯于为数字服务付费，对交互体验、技术信任感要求高，对传统中介模式的信任度较低。
            </p>
            <p className="text-primary font-medium">
              对房都督AI的利好：该群体是SaaS产品和为"效率"、"确定性"付费的天然用户。他们易于理解并欣赏"过程可视化"的科技感与诚实感，是产品的早期采纳者与口碑传播者。
            </p>
          </div>
          
          <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
            <h4 className="text-lg font-medium mb-2">4. 信息消费升级：从"碎片浏览"到"深度决策支持"</h4>
            <p className="text-gray-700 mb-3">
              知识付费、专业数据服务市场年增速超过15%（参考行业报告），表明用户愿意为能提升决策质量的信息付费。在房产领域，简单的挂牌信息已无法满足需求。
            </p>
            <p className="text-primary font-medium">
              对房都督AI的利好：证明了在房产这一更高客单价的领域，为深度、结构化的决策支持付费的意愿和市场规模已经形成。房都督AI是将"知识付费"模式升级为"决策智能"服务。
            </p>
          </div>
          
          <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
            <h4 className="text-lg font-medium mb-2">5. 市场周期性下行催生新需求</h4>
            <p className="text-gray-700 mb-3">
              在市场上升期，购房者更关注"能不能买到"；在调整期或下行期，购房者更关注"该不该买、会不会买错"，深度调研与风险规避需求反而更加刚性。
            </p>
            <p className="text-primary font-medium">
              对房都督AI的利好：房都督AI的服务在牛市中助力"择优"，在熊市中帮助"避坑"和"寻底"，需求具备一定的抗周期韧性，甚至可能在市场观望情绪浓烈时需求更盛。
            </p>
          </div>
        </div>
      </section>
      
      {/* 用户验证 */}
      <section className="bg-white rounded-lg shadow-md p-8 mb-12 border border-gray-200">
        <h2 className="text-2xl font-medium mb-6">初步用户验证与反馈</h2>
        <p className="text-gray-700 leading-relaxed mb-6">
          在商业计划形成的同时，我们通过定向访谈、概念演示与原型测试等方式，对50名精准目标用户（包括潜在购房者、房产投资者及少量从业者）进行了初期验证。核心目的在于测试关键商业假设，特别是用户对"过程可视化"这一核心创新的接受度与付费意愿。
        </p>
        
        <div className="space-y-6">
          <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
            <h4 className="text-lg font-medium mb-3">关键验证发现</h4>
            <ul className="space-y-3">
              <li className="flex items-start">
                <span className="text-primary mr-2">•</span>
                <span className="text-gray-700">
                  <strong>核心痛点的真实性验证：</strong> 92% 的受访者（46人）对"信息矛盾与验证困难"表示强烈共鸣。平均自估耗时：用户回忆其上一次重大房产决策，信息搜集平均耗费 42小时（约5个完整工作日）。
                </span>
              </li>
              <li className="flex items-start">
                <span className="text-primary mr-2">•</span>
                <span className="text-gray-700">
                  <strong>对"过程可视化"创新点的接受度：</strong> 86% 的受访者（43人）在观看Demo后，认为"能看到AI工作过程"会显著提升他们对最终报告结论的信任度。其中， 70% 的人表示这种形式"新颖、直观、让人更放心"。
                </span>
              </li>
              <li className="flex items-start">
                <span className="text-primary mr-2">•</span>
                <span className="text-gray-700">
                  <strong>付费意愿与定价敏感度：</strong> 68% 的受访者（34人）明确表示，如果服务能达到演示效果，愿意为此付费。价格接受区间：对于一份针对单一小区的深度报告，用户接受度最高的价格区间为 88-188元/次。对于包年服务，接受度集中在 399-699元/年。
                </span>
              </li>
              <li className="flex items-start">
                <span className="text-primary mr-2">•</span>
                <span className="text-gray-700">
                  <strong>功能优先级与担忧：</strong> 最期待功能前三名：1. 多平台价格对比与真实性核验（98%）；2. 历史成交趋势分析（90%）；3. 学区、交通等配套客观评分（85%）。主要担忧：数据覆盖的全面性和更新时效性。
                </span>
              </li>
            </ul>
          </div>
        </div>
      </section>
      
      {/* 联系我们 */}
      <section className="bg-white rounded-lg shadow-md p-8 border border-gray-200">
        <h2 className="text-2xl font-medium mb-6">联系我们</h2>
        <p className="text-gray-700 leading-relaxed mb-6">
          如果您对房都督AI有任何问题或建议，欢迎随时联系我们。我们期待与您一起探索房产科技的未来。
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-gray-50 p-6 rounded-lg border border-gray-200 text-center">
            <h4 className="text-lg font-medium mb-2">电子邮件</h4>
            <p className="text-gray-700">contact@fangtanai.com</p>
          </div>
          <div className="bg-gray-50 p-6 rounded-lg border border-gray-200 text-center">
            <h4 className="text-lg font-medium mb-2">电话</h4>
            <p className="text-gray-700">+86 123 4567 8910</p>
          </div>
          <div className="bg-gray-50 p-6 rounded-lg border border-gray-200 text-center">
            <h4 className="text-lg font-medium mb-2">地址</h4>
            <p className="text-gray-700">上海市浦东新区张江高科技园区</p>
          </div>
        </div>
      </section>
    </div>
  )
}

export default About