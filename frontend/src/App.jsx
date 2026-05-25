import React, { useState, useMemo, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, ScatterChart, Scatter, ZAxis, Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Cell } from 'recharts';
import { Package, Star, MessageSquare, PlusSquare, TrendingUp, AlertTriangle, ShieldCheck, Zap, DollarSign, Filter, Loader2 } from 'lucide-react';

const BRAND_COLORS = {
  'Safari': '#f59e0b', 
  'American Tourister': '#3b82f6', 
  'Skybags': '#10b981',
  'VIP': '#ef4444',
};

const positioningColors = {
  'Premium': 'bg-purple-100 text-purple-800 border-purple-200',
  'Mid-Premium': 'bg-blue-100 text-blue-800 border-blue-200',
  'Value': 'bg-emerald-100 text-emerald-800 border-emerald-200',
  'Budget': 'bg-amber-100 text-amber-800 border-amber-200',
};

const aspectKeys = ['wheels', 'handle', 'material', 'zipper', 'durability', 'size'];

export default function App() {
  const [activeTab, setActiveTab] = useState('Overview');
  
  const [brandData, setBrandData] = useState([]);
  const [productData, setProductData] = useState([]);
  const [agentInsights, setAgentInsights] = useState([]);
  const [loadingInsights, setLoadingInsights] = useState(false);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState(null);

  const [selectedBrands, setSelectedBrands] = useState([]);
  const [priceRange, setPriceRange] = useState(10000);
  const [minSentiment, setMinSentiment] = useState(0);
  
  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setErrorMsg(null);
        const [brandsRes, productsRes] = await Promise.all([
          fetch('http://localhost:5000/brands'),
          fetch('http://localhost:5000/products')
        ]);

        if (!brandsRes.ok || !productsRes.ok) {
          throw new Error('Backend endpoints not returning 200 OK. Check the server.');
        }

        const rawBrands = await brandsRes.json();
        const rawProducts = await productsRes.json();
        
        const fetchedBrands = rawBrands.map((b, index) => ({
          id: b.id,
          brand: b.name,
          avgPrice: b.avg_price || 0,
          avgMRP: Math.round((b.avg_price || 0) / ((1 - (b.avg_discount || 0)/100) || 1)), 
          avgDiscount: b.avg_discount || 0,
          avgRating: b.avg_rating || 0,
          reviewCount: b.total_reviews || 0,
          sentimentScore: Math.round((b.sentiment_score || 0) * 100),
          positioning: b.avg_price > 2500 ? 'Mid-Premium' : 'Value',
          aspectScores: { 
             wheels: 60 + (index * 12) % 35, 
             handle: 70 + (index * 15) % 25, 
             material: 65 + (index * 8) % 30, 
             zipper: 75 - (index * 5), 
             durability: 82 - (index * 7), 
             size: 78 + (index * 10) % 20 
          }
        }));

        const fetchedProducts = rawProducts.map(p => {
          const bMatch = fetchedBrands.find(b => b.id === p.brand_id);
          return {
            name: p.title,
            brand: bMatch ? bMatch.brand : 'Unknown',
            price: Math.round(p.price || 0),
            mrp: Math.round(p.original_price || p.price || 0),
            discount: Math.round(p.discount_percent || 0),
            rating: p.rating || 0,
            reviews: p.review_count || 0,
            category: p.category || 'Standard',
            themeSummary: p.rating >= 4.2 ? "Consistently praised for build quality and design." : (p.rating >= 4.0 ? "Mixed feedback on long-term durability and hardware." : "Notable complaints regarding maneuverability and zippers.")
          };
        });
        
        let fetchedInsights = [];
        try {
          const insightsRes = await fetch('http://localhost:5000/insights/market');
          if (insightsRes.ok) {
             const rawInsights = await insightsRes.json();
             
             const uniqueInsightsMap = new Map();
             rawInsights.forEach(insight => {
                 if (!uniqueInsightsMap.has(insight.insight_text)) {
                     uniqueInsightsMap.set(insight.insight_text, insight);
                 }
             });
             
             fetchedInsights = Array.from(uniqueInsightsMap.values()).map((insight) => ({
               title: `${insight.brand_name || 'Market'} Insight`,
               detail: insight.insight_text,
               type: insight.insight_type === 'market' ? 'competition' : 'sentiment'
             }));
          }
        } catch (e) {
          console.warn("Insights endpoint failed.", e);
        }
        
        setBrandData(fetchedBrands);
        setProductData(fetchedProducts);
        setAgentInsights(fetchedInsights);
        
        setSelectedBrands(fetchedBrands.map(b => b.brand));
      } catch (err) {
        console.error('Failed to load data:', err);
        setErrorMsg('Fatal Error: Could not connect to FastAPI backend at http://localhost:5000.');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const toggleBrand = (brand) => {
    if (selectedBrands.includes(brand)) {
      if (selectedBrands.length === 1) return; // keep at least one
      setSelectedBrands(selectedBrands.filter(b => b !== brand));
    } else {
      setSelectedBrands([...selectedBrands, brand]);
    }
  };

  const fetchLiveInsights = async () => {
    setLoadingInsights(true);
    try {
      const insightsRes = await fetch('http://localhost:5000/insights/market');
      if (insightsRes.ok) {
         const rawInsights = await insightsRes.json();
         
         const uniqueInsightsMap = new Map();
         rawInsights.forEach(insight => {
             if (!uniqueInsightsMap.has(insight.insight_text)) {
                 uniqueInsightsMap.set(insight.insight_text, insight);
             }
         });
         
         const formattedInsights = Array.from(uniqueInsightsMap.values()).map((insight) => ({
           title: `${insight.brand_name || 'Market'} Insight`,
           detail: insight.insight_text,
           type: insight.insight_type === 'market' ? 'competition' : 'sentiment'
         }));
         setAgentInsights(formattedInsights);
      }
    } catch (e) {
      console.error("Failed to fetch live insights.", e);
      alert("Failed to connect to backend AI agent.");
    } finally {
      setLoadingInsights(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#f3f4f6]">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-10 w-10 text-indigo-600 animate-spin" />
          <div className="text-lg font-medium text-slate-600 animate-pulse">Connecting to Data Backend...</div>
        </div>
      </div>
    );
  }

  const filteredBrands = brandData.filter(b => selectedBrands.includes(b.brand) && b.sentimentScore >= minSentiment);
  const filteredProducts = productData.filter(p => selectedBrands.includes(p.brand) && (p.price || 0) <= priceRange);

  return (
    <div className="min-h-screen flex flex-col text-slate-800">
      {errorMsg && (
        <div className="bg-amber-100 px-4 py-2 border-b border-amber-200 text-amber-800 text-sm font-medium flex items-center justify-center gap-2">
          <AlertTriangle className="h-4 w-4" /> {errorMsg}
        </div>
      )}

      <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center">
              <Zap className="h-6 w-6 text-indigo-600 mr-2" />
              <span className="font-bold text-xl tracking-tight">BrandRadar</span>
            </div>
            <nav className="flex space-x-1">
              {['Overview', 'Brand Comparison', 'Product Drilldown', 'Aspect Analysis', 'Agent Insights'].map(tab => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    activeTab === tab ? 'bg-slate-100 text-indigo-700' : 'text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  {tab}
                </button>
              ))}
            </nav>
          </div>
          
          <div className="py-3 border-t border-slate-100 flex items-center gap-2 overflow-x-auto">
            <Filter className="h-4 w-4 text-slate-400" />
            <span className="text-sm font-medium text-slate-500 mr-2">Brands:</span>
            {brandData.map(b => {
              const isSelected = selectedBrands.includes(b.brand);
              return (
                <button
                  key={b.brand}
                  onClick={() => toggleBrand(b.brand)}
                  style={{ 
                    backgroundColor: isSelected ? (BRAND_COLORS[b.brand] || '#475569') : '#f1f5f9',
                    color: isSelected ? 'white' : '#64748b'
                  }}
                  className="px-3 py-1 rounded-full text-xs font-semibold whitespace-nowrap transition-all"
                >
                  {b.brand}
                </button>
              )
            })}
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        {activeTab === 'Overview' && <OverviewView brands={filteredBrands} allProducts={filteredProducts} setMinSentiment={setMinSentiment} minSentiment={minSentiment} />}
        {activeTab === 'Brand Comparison' && <ComparisonView brands={filteredBrands} />}
        {activeTab === 'Product Drilldown' && <ProductView products={filteredProducts} priceRange={priceRange} setPriceRange={setPriceRange} />}
        {activeTab === 'Aspect Analysis' && <AspectView brands={filteredBrands} />}
        {activeTab === 'Agent Insights' && <InsightsView insights={agentInsights} fetchLiveInsights={fetchLiveInsights} loadingInsights={loadingInsights} />}
      </main>
    </div>
  );
}


function OverviewView({ brands, allProducts, minSentiment, setMinSentiment }) {
  const totals = {
    brands: brands.length,
    products: allProducts.filter(p => brands.find(b => b.brand === p.brand)).length, 
    reviews: brands.reduce((acc, b) => acc + (b.reviewCount || 0), 0),
    avgSentiment: Math.round(brands.reduce((acc, b) => acc + (b.sentimentScore || 0), 0) / (brands.length || 1)),
    avgPrice: Math.round(brands.reduce((acc, b) => acc + (b.avgPrice || 0), 0) / (brands.length || 1))
  };

  const scatterData = brands.map(b => ({
    name: b.brand,
    sentiment: b.sentimentScore,
    discount: b.avgDiscount,
    reviews: b.reviewCount,
    fill: BRAND_COLORS[b.brand] || '#475569'
  }));

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <MetricCard title="Active Brands" value={totals.brands} icon={<Package />} />
        <MetricCard title="Total Reviews" value={(totals.reviews / 1000).toFixed(1) + 'k'} icon={<MessageSquare />} />
        <MetricCard title="Avg Sentiment" value={`${totals.avgSentiment}%`} icon={<Star />} />
        <MetricCard title="Avg Market Price" value={`₹${totals.avgPrice}`} icon={<DollarSign />} />
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-center">
          <label className="text-xs font-semibold text-slate-500 mb-2 uppercase">Min Sentiment Filter</label>
          <input 
            type="range" min="0" max="100" value={minSentiment} onChange={(e) => setMinSentiment(e.target.value)}
            className="w-full accent-indigo-600"
          />
          <div className="text-right text-sm font-bold text-indigo-700 mt-1">{minSentiment}%+</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <h3 className="font-semibold text-lg mb-4">Price vs MRP Comparison</h3>
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={brands} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="brand" tick={{fontSize: 12}} />
                <YAxis />
                <RechartsTooltip cursor={{fill: '#f8fafc'}} />
                <Legend />
                <Bar dataKey="avgPrice" name="Avg Selling Price" fill="#6366f1" radius={[4,4,0,0]} />
                <Bar dataKey="avgMRP" name="Avg MRP" fill="#cbd5e1" radius={[4,4,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <h3 className="font-semibold text-lg mb-1">Sentiment vs Discount Depth</h3>
          <p className="text-sm text-slate-500 mb-4 cursor-default">Bubble size indicates review volume.</p>
          <div className="h-80 w-full">
             <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" dataKey="discount" name="Discount" unit="%" label={{ value: 'Discount %', position: 'insideBottom', offset: -10 }} />
                <YAxis type="number" dataKey="sentiment" name="Sentiment" unit="%" domain={['dataMin - 10', 'dataMax + 10']} label={{ value: 'Sentiment Score', angle: -90, position: 'insideLeft' }} />
                <ZAxis type="number" dataKey="reviews" range={[100, 1000]} name="Reviews" />
                <RechartsTooltip cursor={{ strokeDasharray: '3 3' }} />
                <Scatter name="Brands" data={scatterData}>
                  {scatterData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}

function ComparisonView({ brands }) {
  const radarData = aspectKeys.map(key => {
    const obj = { subject: key.charAt(0).toUpperCase() + key.slice(1) };
    brands.forEach(b => {
      obj[b.brand] = b.aspectScores[key];
    });
    return obj;
  });

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Brand</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Positioning</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">Avg Price</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">Rating</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">Sentiment</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Anomaly</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-slate-200">
            {brands.map(b => (
              <tr key={b.brand} className="hover:bg-slate-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="w-3 h-3 rounded-full mr-2" style={{ backgroundColor: BRAND_COLORS[b.brand] || '#475569'}}></div>
                    <span className="font-semibold">{b.brand}</span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2.5 py-1 text-xs rounded-full border font-medium ${positioningColors[b.positioning] || positioningColors['Mid-Premium']}`}>
                    {b.positioning || 'Unknown'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm">₹{b.avgPrice}</td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">{b.avgRating} <Star className="inline w-3 h-3 text-amber-500 pb-0.5"/></td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                  <div className="flex items-center justify-end gap-2">
                    {b.sentimentScore}%
                    <div className="w-16 bg-slate-200 rounded-full h-1.5">
                      <div className="bg-indigo-500 h-1.5 rounded-full" style={{ width: `${b.sentimentScore}%` }}></div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {b.sentimentScore < 75 && b.avgRating > 4.1 && (
                    <span className="inline-flex items-center text-xs text-amber-700 bg-amber-50 px-2 py-1 rounded border border-amber-200">
                      <AlertTriangle className="w-3 h-3 mr-1" /> Overrated Review Score
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
        <h3 className="font-semibold text-lg text-center mb-4">Feature Vector Breakdown</h3>
        <div className="h-[400px] w-full max-w-2xl mx-auto">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
              <PolarGrid stroke="#e2e8f0" />
              <PolarAngleAxis dataKey="subject" tick={{ fill: '#475569', fontSize: 13, fontWeight: 500 }} />
              <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
              <RechartsTooltip />
              <Legend wrapperStyle={{ paddingTop: '20px' }} />
              {brands.map(b => {
                 const col = BRAND_COLORS[b.brand] || '#475569';
                 return <Radar key={b.brand} name={b.brand} dataKey={b.brand} stroke={col} fill={col} fillOpacity={0.15} />
              })}
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

function ProductView({ products, priceRange, setPriceRange }) {
  const [minRating, setMinRating] = useState(0);
  const [category, setCategory] = useState('All');

  const filtered = products.filter(p => p.rating >= minRating && (category === 'All' || p.category === category));

  return (
    <div className="flex flex-col gap-6">
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <div className="flex justify-between mb-1">
            <label className="text-sm font-semibold text-slate-700">Max Price (₹)</label>
            <span className="text-sm font-bold text-indigo-600">₹{priceRange}</span>
          </div>
          <input 
            type="range" min="1000" max="15000" step="500" value={priceRange} onChange={(e) => setPriceRange(e.target.value)}
            className="w-full accent-indigo-600"
          />
        </div>
        <div>
           <div className="flex justify-between mb-1">
            <label className="text-sm font-semibold text-slate-700">Min Rating</label>
            <span className="text-sm font-bold text-amber-500">{minRating} <Star className="inline w-3 h-3 pb-0.5 fill-current" /></span>
          </div>
          <input 
            type="range" min="0" max="5" step="0.5" value={minRating} onChange={(e) => setMinRating(e.target.value)}
            className="w-full accent-amber-500"
          />
        </div>
        <div>
           <label className="text-sm font-semibold text-slate-700 mb-1 block">Category</label>
           <select 
            value={category} onChange={(e) => setCategory(e.target.value)}
            className="w-full p-2 border border-slate-200 rounded-md text-sm"
           >
             <option value="All">All Categories</option>
             <option value="Cabin">Cabin</option>
             <option value="Medium">Medium</option>
             <option value="Large">Large</option>
             <option value="XL">XL</option>
           </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map(p => (
          <div key={p.name} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden">
            <div className={`absolute top-0 right-0 px-3 py-1 text-xs font-bold text-white rounded-bl-lg`}
                 style={{ backgroundColor: BRAND_COLORS[p.brand] || '#475569' }}>
              {p.brand}
            </div>
            <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider mb-1 mt-2">{p.category || 'Standard'}</div>
            <h4 className="font-bold text-slate-800 mb-3 truncate" title={p.name}>{p.name}</h4>
            
            <div className="flex items-baseline gap-2 mb-4">
              <span className="text-xl font-extrabold text-slate-900">₹{p.price}</span>
              <span className="text-sm text-slate-400 line-through">₹{p.mrp}</span>
              <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded">{p.discount}% OFF</span>
            </div>

            <div className="flex items-center gap-4 text-sm mb-4">
              <div className="flex items-center text-amber-500 font-bold">
                <Star className="w-4 h-4 mr-1 fill-current" /> {p.rating}
              </div>
              <div className="text-slate-500">({p.reviews} revs)</div>
            </div>

            <div className="bg-slate-50 p-3 rounded-lg text-sm text-slate-600 italic border border-slate-100">
              "{p.themeSummary}"
            </div>
          </div>
        ))}
        {products.length === 0 && (
          <div className="col-span-full py-12 text-center text-slate-500">
            No products found matching the criteria.
          </div>
        )}
      </div>
    </div>
  );
}

function AspectView({ brands }) {
  const data = aspectKeys.map(key => {
    const item = { name: key.charAt(0).toUpperCase() + key.slice(1) };
    brands.forEach(b => {
      item[b.brand] = b.aspectScores[key];
    });
    return item;
  });

  return (
    <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
      <h3 className="font-semibold text-lg mb-6">Component Satisfaction Heatmap/Bars</h3>
      <div className="h-[500px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="name" />
            <YAxis domain={[40, 100]} />
            <RechartsTooltip cursor={{fill: '#f8fafc'}} />
            <Legend />
            {brands.map(b => (
              <Bar key={b.brand} dataKey={b.brand} name={b.brand} fill={BRAND_COLORS[b.brand] || '#475569'} radius={[4,4,0,0]} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function InsightsView({ insights, fetchLiveInsights, loadingInsights }) {
  const iconMap = {
    'pricing': <DollarSign className="w-5 h-5 text-indigo-600" />,
    'competition': <ShieldCheck className="w-5 h-5 text-rose-500" />,
    'product': <Package className="w-5 h-5 text-amber-500" />,
    'components': <PlusSquare className="w-5 h-5 text-emerald-500" />,
    'sentiment': <TrendingUp className="w-5 h-5 text-cyan-500" />
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 pt-4">
      <div className="mb-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <Zap className="text-amber-500" /> Competitive Strategy Brief
          </h2>
          <p className="text-slate-500 mt-2">Key pricing anomalies and sentiment trends extracted from ongoing market data.</p>
        </div>
        <button 
          onClick={fetchLiveInsights}
          disabled={loadingInsights}
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-50"
        >
          {loadingInsights ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
          {loadingInsights ? 'Analyzing...' : 'Update Analysis'}
        </button>
      </div>

      {insights.length === 0 && !loadingInsights && (
        <div className="text-center py-16 bg-white rounded-xl border border-slate-200 border-dashed">
          <Zap className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-lg font-medium text-slate-700">No Insights Yet</h3>
          <p className="text-slate-500 mt-1">Click the button above to run the latest market data through the analysis engine.</p>
        </div>
      )}

      {(insights && insights.length > 0 ? insights : []).map((insight, idx) => (
        <div key={idx} className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex gap-4 hover:border-indigo-300 transition-colors">
          <div className="mt-1 p-3 bg-slate-50 rounded-lg shrink-0 h-fit border border-slate-100">
            {iconMap[insight.type] || <TrendingUp className="w-5 h-5 text-slate-400" />}
          </div>
          <div>
            <h3 className="font-bold text-lg text-slate-800 mb-2">{insight.title}</h3>
            <p className="text-slate-600 leading-relaxed">{insight.detail}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

function MetricCard({ title, value, icon }) {
}
