module.exports = { 
  "base" : "/",
  "description" : "来自思源笔记的内容",
  "head" : [ [ 
        "link",
        { 
          "href" : "/images/logo.png",
          "rel" : "icon"
        }
      ] ],
  "lang" : "zh-CN",
  "themeConfig" : { 
      "logo" : "/images/logo.png",
      "nav" : [ 
          { 
            "link" : "/",
            "text" : "首页"
          },
          { 
            "items" : [ { 
                  "link" : "/测试笔记/",
                  "text" : "测试笔记"
                } ],
            "text" : "来自思源笔记"
          }
        ],
      "sidebar" : { "/测试笔记/" : [{title: '测试笔记', path: '/测试笔记/', children: [{title: '一层笔记1', path: '/测试笔记/一层笔记1/', children: [{title: '二层笔记1.1', path: '/测试笔记/一层笔记1/二层笔记1.1'}, {title: '二层笔记1.2', path: '/测试笔记/一层笔记1/二层笔记1.2'}]}, {title: '一层笔记2', path: '/测试笔记/一层笔记2/', children: [{title: '二层笔记2.1', path: '/测试笔记/一层笔记2/二层笔记2.1/', children: [{title: '三层笔记2.1.1', path: '/测试笔记/一层笔记2/二层笔记2.1/三层笔记2.1.1'}]}]}, {title: '一层笔记3', path: '/测试笔记/一层笔记3'}]}] },
      "sidebarDepth" : 2
    },
  "title" : "思源笔记"
}
