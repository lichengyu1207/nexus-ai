export interface BrandCopy {
  hero: {
    mainTitle: string;
    subTitle: string;
  };
  consulting: {
    mainTitle: string;
    subTitle: string;
  };
  brandManual: {
    mainTitle: string;
    subTitle: string;
  };
  slogan: {
    main: string;
    simplified: string;
    alternative: string;
  };
  story: string[];
}

export const brandCopy: BrandCopy = {
  hero: {
    mainTitle: '买房，别再瞎猜了。',
    subTitle: 'AI多智能体，把你的决策变成明牌。',
  },
  consulting: {
    mainTitle: '你的命盘，我算；你的房产，我断。',
    subTitle: '周瑜陆逊，给你当军师。',
  },
  brandManual: {
    mainTitle: '让房子听你的话，让命运跟你走。',
    subTitle: '三省六部智能体，为你一个人服务。',
  },
  slogan: {
    main: '听见世界，消弭隔阂，让沟通精准直达。以科技，让世界同频。',
    simplified: '听见世界，同步未来',
    alternative: '房都督——你的AI智囊，帮你把问题走成答案。',
  },
  story: [
    '中国有句老话：一命二运三风水，四积阴德五读书。',
    '现在，你多了第六个选择——房都督。',
    '',
    '我们把周瑜、陆逊从三国拉回来，给你当军师。',
    '一个管战略，一个管细节，后面还藏着六部智能体，替你跑数据、算估值、挖记忆、防风险。',
    '你只管问，剩下的事，它们干。',
    '',
    '我们不谈玄学，只讲逻辑。',
    '你的命盘，我们拆成六维；你的房子，我们算到个位数。',
    '报告里每一句话，都有据可查；每一步推理，都摆给你看。',
    '',
    '这不是算命，这是用AI把你的路，一条条画出来。',
    '房都督，让你在人生最重要的决定上，不再拍脑袋。',
  ],
};

export type CopyScenario = 'hero' | 'consulting' | 'brandManual';

export function getCopyForScenario(scenario: CopyScenario) {
  return brandCopy[scenario];
}

export default brandCopy;
