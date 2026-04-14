export default function TierList() {
  return (
    <main className="pt-24 pb-12 px-8 min-h-screen">
      <div className="max-w-7xl mx-auto">
        {/* Hero Header Section */}
        <header className="mb-12">
          <h1 className="text-6xl font-bold tracking-tighter text-on-surface mb-4">
            Champion Tier List
          </h1>
          <p className="text-on-surface-variant max-w-3xl leading-relaxed text-lg">
            Checking how your main is performing in latest patch or looking for a new one? With our tier list you are sure to always stay up to date
            which latest meta! 
          </p>
        </header>

        {/* Filter & Sorting Bar */}
        <section className="bg-surface-container-low p-1 rounded-lg mb-8 border border-outline-variant/10">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-1">
            <div className="bg-surface-container p-5 flex flex-col gap-1 hover:bg-surface-container-high transition-colors cursor-pointer">
              <span className="text-[10px] text-on-surface-variant uppercase tracking-widest font-label font-bold">
                Server Region
              </span>
              <div className="flex justify-between items-center">
                <span className="font-medium text-on-surface">Korea (KR)</span>
                <span
                  className="material-symbols-outlined text-primary"
                  data-icon="expand_more"
                >
                  expand_more
                </span>
              </div>
            </div>
            <div className="bg-surface-container p-5 flex flex-col gap-1 hover:bg-surface-container-high transition-colors cursor-pointer">
              <span className="text-[10px] text-on-surface-variant uppercase tracking-widest font-label font-bold">
                Role / Position
              </span>
              <div className="flex justify-between items-center">
                <span className="font-medium text-on-surface">
                  Jungle
                </span>
                <span
                  className="material-symbols-outlined text-primary"
                  data-icon="filter_list"
                >
                  filter_list
                </span>
              </div>
            </div>
            <div className="bg-surface-container p-5 flex flex-col gap-1 hover:bg-surface-container-high transition-colors cursor-pointer">
              <span className="text-[10px] text-on-surface-variant uppercase tracking-widest font-label font-bold">
                Competitive Rank
              </span>
              <div className="flex justify-between items-center">
                <span className="font-medium text-on-surface">Challenger</span>
              </div>
            </div>
            <div className="bg-surface-container p-5 flex flex-col gap-1 hover:bg-surface-container-high transition-colors cursor-pointer">
              <span className="text-[10px] text-on-surface-variant uppercase tracking-widest font-label font-bold">
                Patch Version
              </span>
              <div className="flex justify-between items-center">
                <span className="font-medium text-primary">
                  v14.04.1
                </span>
                <span
                  className="material-symbols-outlined text-primary"
                  data-icon="update"
                >
                  update
                </span>
              </div>
            </div>
          </div>
        </section>

        {/* Expanded Data Table */}
        <div className="bg-surface-container rounded-sm overflow-hidden relative border border-outline-variant/10">
          {/* Signature Gradient Light Leak */}
          <div className="absolute top-0 left-0 w-96 h-96 bg-gradient-to-br from-primary/10 to-transparent blur-[100px] pointer-events-none"></div>
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-outline-variant/15 text-[10px] text-on-surface-variant uppercase tracking-[0.2em] font-label font-bold bg-surface-container-high/30">
                <th className="px-8 py-6">Rank</th>
                <th className="px-8 py-6">Champion</th>
                <th className="px-8 py-6">Win Rate</th>
                <th className="px-8 py-6">Pick Rate</th>
                <th className="px-8 py-6">Ban Rate</th>
                <th className="px-8 py-6 text-right">Best Synergy</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant/10">
              {/* S+ Tier Rows */}
              <tr className="hover:bg-primary/5 transition-colors group">
                <td className="px-8 py-7">
                  <span className="text-primary px-3 py-1 text-sm font-black tracking-tighter">
                    S+
                  </span>
                </td>
                <td className="px-8 py-7">
                  <div className="flex items-center gap-5">
                    <div className="w-12 h-12 rounded-sm bg-surface-container-high overflow-hidden border border-primary/30">
                      <img
                        className="w-full h-full object-cover"
                        alt="Stylized esports character portrait"
                        src="https://lh3.googleusercontent.com/aida-public/AB6AXuBfyPy1Nak7gW9_1AmSN1v7AJX7K0J2d6l42vSvNEtts_0IT8uxjzivv0GVQWXLtTUBrMsdwgubdofOa2mFxl5IZ285_hFCLo5xOigZVW7rOpXFWEW2KO9d7AniOVDNBtIONESkbsgyaRwucq6kSwSF9FXRZ589kIruNt2j8JnKF4DK8F-aQWgdaHCn8RXs9vHQCKL_-W8yWPe-zKqqzw9ZI1XLtY5UDXY7jAd875g1s9465Xw5gC0Ma4NHDxLbLRUBUE2nkombSCg"
                      />
                    </div>
                    <div>
                      <div className="text-on-surface font-bold text-lg leading-tight uppercase">
                        Lee Sin
                      </div>
                      <div className="text-[10px] text-on-surface-variant tracking-widest uppercase mt-1">
                        The Blind Monk
                      </div>
                    </div>
                  </div>
                </td>
                <td className="px-8 py-7">
                  <div className="flex items-center gap-4">
                    <span className="font-bold text-primary text-xl">
                      54.2%
                    </span>
                    <div className="w-16 h-1.5 bg-surface-container-low rounded-full overflow-hidden">
                      <div className="h-full bg-primary w-[54.2%]"></div>
                    </div>
                  </div>
                </td>
                <td className="px-8 py-7 text-on-surface font-medium">12.8%</td>
                <td className="px-8 py-7 text-error/90 font-bold">45.1%</td>
                <td className="px-8 py-7">
                  <div className="flex justify-end -space-x-2">
                    <div className="w-10 h-10 rounded-full border-2 border-surface-container bg-surface-container-high overflow-hidden">
                      <img
                        alt="Avatar"
                        src="https://lh3.googleusercontent.com/aida-public/AB6AXuA5aDXF5Ht3L8lcGK3zs8ne89CPYpWqwzpeiljBTkger7si18WKbWc3JiM06BN3o-XgnuKtyBNHrKb6gmloRtheN8aFJ6qcprOS_pB6yzKLuMzQl9d8doMBjiuwt-BchxxfnEPMfGvON51c2r-1cvuP1b2CIGfbwcsea3HkNiDWlPkBj4MFd_v03xkKjrTybtBT0M2sYLybWBRU7YLAdrL0btCNnsohESJ_-ww9a1BRERGXd_5ZIBxDIWWT3RSgcmg2R6TPeyYcmH0"
                      />
                    </div>
                    <div className="w-10 h-10 rounded-full border-2 border-surface-container bg-surface-container-high overflow-hidden">
                      <img
                        alt="Avatar"
                        src="https://lh3.googleusercontent.com/aida-public/AB6AXuC6Hj05i14wg3Fd0-dWStL895LKF6Ju5COI444lNmTNgNDsuGN_ajsjGeK_oiZBpoeggbW7wO0pCzKLO6r8-ghpK0lE03uk1lk07rzvt_77WUUVy7NUWJhhL_VABJSTJm03U34OxZ1U2LHrka5m_QTT87YvR1--KgseLu7rB3ti-TrjqVYl3vTfDByWFprTDAIUNMUZKgJpjnT0ce9vUjWa8NyEcmMxhbPxmTPoZFNoX8VngxrViAoygjUJTX_6md3zHqSGAcHE1lU"
                      />
                    </div>
                  </div>
                </td>
              </tr>

              {/* S Tier Row */}
              <tr className="hover:bg-primary/5 transition-colors group">
                <td className="px-8 py-7">
                  <span className="text-primary-dim px-3 py-1 text-sm font-bold tracking-tighter">
                    S
                  </span>
                </td>
                <td className="px-8 py-7">
                  <div className="flex items-center gap-5">
                    <div className="w-12 h-12 rounded-sm bg-surface-container-high overflow-hidden border border-outline-variant/30">
                      <img
                        className="w-full h-full object-cover"
                        alt="Character portrait"
                        src="https://lh3.googleusercontent.com/aida-public/AB6AXuCsq4aQBgdyvVqeLmEYFaotUZSwmJpKIoiWuWLqyVWAoILT-NJ6RDz_51dhmFUHrn-DSHQcvB5FX-oaSOdon-ak2kh0y08PJUgVV2_Nu8z4KBe59Jdf0cy8l7QybKHamVG_6KKg3c7D8_7QQfUIkUNpj-f35MispgcJg5tWDcDpX8U0Qi2wwOIaK_juocvkQrwj66cuvtln9eQ1rV17x_IZnvIleHZn03MT4DL7hfX9LRNVYz-5A9wotICxLuW7pngWA-otSI7mfqc"
                      />
                    </div>
                    <div>
                      <div className="text-on-surface font-bold text-lg leading-tight uppercase">
                        Nidalee
                      </div>
                      <div className="text-[10px] text-on-surface-variant tracking-widest uppercase mt-1">
                        The Bestial Huntress
                      </div>
                    </div>
                  </div>
                </td>
                <td className="px-8 py-7">
                  <div className="flex items-center gap-4">
                    <span className="font-bold text-on-surface text-xl">
                      52.8%
                    </span>
                    <div className="w-16 h-1.5 bg-surface-container-low rounded-full overflow-hidden">
                      <div className="h-full bg-primary-dim w-[52.8%]"></div>
                    </div>
                  </div>
                </td>
                <td className="px-8 py-7 text-on-surface font-medium">9.4%</td>
                <td className="px-8 py-7 text-on-surface-variant font-medium">
                  32.2%
                </td>
                <td className="px-8 py-7 text-right">
                  <div className="flex justify-end">
                    <div className="w-10 h-10 rounded-full border-2 border-surface-container bg-surface-container-high overflow-hidden">
                      <img
                        alt="Avatar"
                        src="https://lh3.googleusercontent.com/aida-public/AB6AXuAAPaWQGHDjzWD_JxVchJ93h04C7YyPua-zqmawEeD9zIY0562aIlRQ3sp0y2tgsGkCaK7jHXnAkpyZvkR35mIWWePv0FjpAnr-t3Qab1K99ihsgNpdSBxiF_yRXWz4iUxiecVSGniL0Z85ejJIYXWBftosWxaNbT5gZABeru8GWGt2pXuT_b4tyZm6znZ51CIDOCxKXx_m3AUy9S3reX5SemHXejdtF8CWPIVIJ6y3K7Sb_fTv2ojKvyd-GV2DOe5Ecl3-Y1siDPw"
                      />
                    </div>
                  </div>
                </td>
              </tr>

              {/* A Tier Row */}
              <tr className="hover:bg-primary/5 transition-colors group">
                <td className="px-8 py-7">
                  <span className="text-on-surface-variant px-3 py-1 text-sm font-bold tracking-tighter">
                    A
                  </span>
                </td>
                <td className="px-8 py-7">
                  <div className="flex items-center gap-5">
                    <div className="w-12 h-12 rounded-sm bg-surface-container-high overflow-hidden border border-outline-variant/30">
                      <img
                        className="w-full h-full object-cover"
                        alt="Character portrait"
                        src="https://lh3.googleusercontent.com/aida-public/AB6AXuCADD4F5GdDiYzSMGj1PS1X170jE7MdNLfUwdBnZgh5-wxCkGV1uoi2d_nRiKKuJhVBG2pcvOWAOQjTscIDrzEdml691XD7Z6t3ZyF87sGI3VGd91ygG5VVX883dSko2efw91rdXGbmEY015vkoi8eELHF67wq3K49OYUt1NhtbSttMB8ugVmQZOEHqZxcNpeXT9vjELjTUnxHkh37dS_y6lV2ZHlIwyphk0zL-E54GHwDzK9yCIGZUpP2NvA4kG0MoyRsLJg9iZD4"
                      />
                    </div>
                    <div>
                      <div className="text-on-surface font-bold text-lg leading-tight uppercase">
                        Kha'Zix
                      </div>
                      <div className="text-[10px] text-on-surface-variant tracking-widest uppercase mt-1">
                        The Voidreaver
                      </div>
                    </div>
                  </div>
                </td>
                <td className="px-8 py-7">
                  <div className="flex items-center gap-4">
                    <span className="font-bold text-on-surface text-xl">
                      51.1%
                    </span>
                    <div className="w-16 h-1.5 bg-surface-container-low rounded-full overflow-hidden">
                      <div className="h-full bg-outline-variant w-[51.1%]"></div>
                    </div>
                  </div>
                </td>
                <td className="px-8 py-7 text-on-surface font-medium">10.2%</td>
                <td className="px-8 py-7 text-on-surface-variant font-medium">
                  18.5%
                </td>
                <td className="px-8 py-7">
                  <div className="flex justify-end -space-x-2">
                    <div className="w-10 h-10 rounded-full border-2 border-surface-container bg-surface-container-high overflow-hidden">
                      <img
                        alt="Avatar"
                        src="https://lh3.googleusercontent.com/aida-public/AB6AXuCuJ0u54zLNHwrs99hRK7Yh8AT6kls8RCPEafVtIJUGndJ3YZwoA0zaRYvazM6SRFzxG5nDiwKxlG34AhZVkCfCMZKbRPgWUXNGarBAVdy8HyWsjv0pUVJ3RzzaLm3iDjMiHYT8ireYRI0n3RSdShvHW9lESiUInrvv0WtfF0KZNHXs1v-51fdrerS9RgXLH65xfF_rzJxR2YlXNq63RtfYLJFNZ2cRThdFlDgLPlaW7TTy0RzW3_sahUcEdljaGPXkgv1RDETcqpA"
                      />
                    </div>
                    <div className="w-10 h-10 rounded-full border-2 border-surface-container bg-surface-container-high overflow-hidden">
                      <img
                        alt="Avatar"
                        src="https://lh3.googleusercontent.com/aida-public/AB6AXuBwkaiEvZbl0dsUVpyrf-kg1bJ28AZVk5G-3UWnOsauOvW6pYIKvBEBUnLpTtyTY7toHx52uuMvk6WLQS1Mu0WZtvuzsC8-rx6WJ9aoesNm5xpiVp4Ro3w6V_j4KpM9qPYPFWD5Ao98M2GX3UJWv7B3OPAkOCYY3Uzab6pzz71wuvVZ8z1WXqEpnmJ4xtIpU5AsMoMqMnmMzBYgnLGqHYl856iE8pZd3zTSe1uYY80zliLhkAgnPBok7PWd0ZBkz04Araje1eAVXks"
                      />
                    </div>
                  </div>
                </td>
              </tr>

              {/* B Tier Row */}
              <tr className="hover:bg-primary/5 transition-colors group border-b border-outline-variant/10">
                <td className="px-8 py-7">
                  <span className="text-outline px-3 py-1 text-sm font-bold tracking-tighter">
                    B
                  </span>
                </td>
                <td className="px-8 py-7">
                  <div className="flex items-center gap-5">
                    <div className="w-12 h-12 rounded-sm bg-surface-container-high overflow-hidden border border-outline-variant/30">
                      <img
                        className="w-full h-full object-cover"
                        alt="Character portrait"
                        src="https://lh3.googleusercontent.com/aida-public/AB6AXuCQSUIhyboAcgrJ4IjB70hrwHX9uBavI_qvhR6G3MQXf1xTYTQGW6da5fE6CiCV9MvnIIg5_yR8DZdcoUDBuXTbKraCFBFahiqkwgXLYtrdqUPN5ryGOwJtyaEiplnozck21YNTu8E8bkcua2DPK5vFrWm4QqQFiQ7iVd9q831SGUwpIHejkmMpkGH34ntftMxWKC07C75XATTWdmuE4hLy_0VgFjNeZIMS0Sa0w9fXqWp2oGiIK-JyHX7org5fpGD2YBfkYxRkj7w"
                      />
                    </div>
                    <div>
                      <div className="text-on-surface font-bold text-lg leading-tight uppercase">
                        Jarvan IV
                      </div>
                      <div className="text-[10px] text-on-surface-variant tracking-widest uppercase mt-1">
                        Exemplar of Demacia
                      </div>
                    </div>
                  </div>
                </td>
                <td className="px-8 py-7">
                  <div className="flex items-center gap-4">
                    <span className="font-bold text-on-surface text-xl">
                      49.4%
                    </span>
                    <div className="w-16 h-1.5 bg-surface-container-low rounded-full overflow-hidden">
                      <div className="h-full bg-outline-variant/30 w-[49.4%]"></div>
                    </div>
                  </div>
                </td>
                <td className="px-8 py-7 text-on-surface font-medium">7.1%</td>
                <td className="px-8 py-7 text-on-surface-variant font-medium">
                  5.2%
                </td>
                <td className="px-8 py-7 text-right">
                  <span className="text-[10px] text-on-surface-variant tracking-widest uppercase italic">
                    Low Variance
                  </span>
                </td>
              </tr>

              {/* Extended Row 1 */}
              <tr className="hover:bg-primary/5 transition-colors group">
                <td className="px-8 py-7">
                  <span className="text-on-surface-variant px-3 py-1 text-sm font-bold tracking-tighter">
                    B
                  </span>
                </td>
                <td className="px-8 py-7">
                  <div className="flex items-center gap-5">
                    <div className="w-12 h-12 rounded-sm bg-surface-container-high overflow-hidden border border-outline-variant/30">
                      <div className="w-full h-full flex items-center justify-center bg-surface-container-highest text-primary font-bold">
                        VI
                      </div>
                    </div>
                    <div>
                      <div className="text-on-surface font-bold text-lg leading-tight uppercase">
                        Vi
                      </div>
                      <div className="text-[10px] text-on-surface-variant tracking-widest uppercase mt-1">
                        The Piltover Enforcer
                      </div>
                    </div>
                  </div>
                </td>
                <td className="px-8 py-7">
                  <div className="flex items-center gap-4">
                    <span className="font-bold text-on-surface text-xl">
                      48.9%
                    </span>
                    <div className="w-16 h-1.5 bg-surface-container-low rounded-full overflow-hidden">
                      <div className="h-full bg-outline-variant/30 w-[48.9%]"></div>
                    </div>
                  </div>
                </td>
                <td className="px-8 py-7 text-on-surface font-medium">6.5%</td>
                <td className="px-8 py-7 text-on-surface-variant font-medium">
                  4.1%
                </td>
                <td className="px-8 py-7 text-right">
                  <span className="text-primary text-[10px] font-bold uppercase tracking-widest">
                    + Orianna
                  </span>
                </td>
              </tr>

              {/* Extended Row 2 */}
              <tr className="hover:bg-primary/5 transition-colors group">
                <td className="px-8 py-7">
                  <span className="text-error/70 px-3 py-1 text-sm font-bold tracking-tighter">
                    C
                  </span>
                </td>
                <td className="px-8 py-7">
                  <div className="flex items-center gap-5">
                    <div className="w-12 h-12 rounded-sm bg-surface-container-high overflow-hidden border border-outline-variant/30">
                      <div className="w-full h-full flex items-center justify-center bg-surface-container-highest text-on-surface-variant font-bold">
                        GR
                      </div>
                    </div>
                    <div>
                      <div className="text-on-surface font-bold text-lg leading-tight uppercase">
                        Graves
                      </div>
                      <div className="text-[10px] text-on-surface-variant tracking-widest uppercase mt-1">
                        The Outlaw
                      </div>
                    </div>
                  </div>
                </td>
                <td className="px-8 py-7">
                  <div className="flex items-center gap-4">
                    <span className="font-bold text-error text-xl">
                      46.5%
                    </span>
                    <div className="w-16 h-1.5 bg-surface-container-low rounded-full overflow-hidden">
                      <div className="h-full bg-error-container w-[46.5%]"></div>
                    </div>
                  </div>
                </td>
                <td className="px-8 py-7 text-on-surface font-medium">11.2%</td>
                <td className="px-8 py-7 text-on-surface-variant font-medium">
                  21.4%
                </td>
                <td className="px-8 py-7 text-right">
                  <span className="text-[10px] text-on-surface-variant tracking-widest uppercase italic">
                    Declining
                  </span>
                </td>
              </tr>
            </tbody>
          </table>

          {/* Table Footer / Load More */}
          <div className="p-8 flex justify-center bg-surface-container-low/50">
            <button className="px-8 py-3 border border-primary/30 text-primary font-headline font-bold uppercase tracking-widest hover:bg-primary/10 transition-all rounded-sm flex items-center gap-3">
              <span
                className="material-symbols-outlined text-sm"
                data-icon="add"
              >
                add
              </span>
              Load More Strategic Data
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}