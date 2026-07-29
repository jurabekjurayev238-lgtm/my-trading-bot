import React, { useState, useEffect, useCallback } from 'react';
import { ChevronLeft, ChevronRight, Presentation, MonitorPlay, Zap, CheckCircle2 } from 'lucide-react';

export default function App() {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [touchStart, setTouchStart] = useState(null);
  const [touchEnd, setTouchEnd] = useState(null);

  // Slayd ma'lumotlari
  const slides = [
    {
      id: 1,
      layout: 'title',
      title: 'Zamonaviy Taqdimot Shabloni',
      subtitle: 'Taqdimotingizni yanada qiziqarli va professional qiling',
      icon: <Presentation className="w-20 h-20 mb-6 text-blue-400" />
    },
    {
      id: 2,
      layout: 'content',
      title: 'Biz haqimizda',
      content: 'Biz eng soʻnggi texnologiyalardan foydalangan holda qulay va zamonaviy interfeyslar yaratamiz. Maqsadimiz barcha uchun tushunarli va chiroyli dizaynlarni taqdim etishdir.',
      icon: <MonitorPlay className="w-12 h-12 text-purple-400 mb-4" />
    },
    {
      id: 3,
      layout: 'list',
      title: 'Asosiy Xususiyatlar',
      items: [
        'Tez va silliq animatsiyalar',
        'Barcha qurilmalarga mos (Moslashuvchan/Responsive)',
        'Oson tahrirlanadigan kod tuzilmasi',
        'Koʻzni qamashtiruvchi zamonaviy dizayn'
      ],
      icon: <Zap className="w-12 h-12 text-yellow-400 mb-4" />
    },
    {
      id: 4,
      layout: 'title',
      title: 'Eʼtiboringiz uchun rahmat!',
      subtitle: 'Savollaringiz boʻlsa, javob berishdan mamnun boʻlamiz.',
      icon: <CheckCircle2 className="w-20 h-20 mb-6 text-green-400" />
    }
  ];

  const lastIndex = slides.length - 1;

  // Funksional yangilash => eskirgan closure muammosi yo'q,
  // shuning uchun klaviatura listenerini qayta ro'yxatdan o'tkazish shart emas.
  const nextSlide = useCallback(() => {
    setCurrentSlide((s) => (s < lastIndex ? s + 1 : s));
  }, [lastIndex]);

  const prevSlide = useCallback(() => {
    setCurrentSlide((s) => (s > 0 ? s - 1 : s));
  }, []);

  // Klaviatura orqali boshqarish
  useEffect(() => {
    const handleKeyDown = (e) => {
      // DIQQAT: probel uchun e.key = ' ' (bo'sh joy). 'Space' — bu e.code.
      if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown') {
        e.preventDefault();            // probel sahifani pastga surmasin
        nextSlide();
      } else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
        e.preventDefault();
        prevSlide();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [nextSlide, prevSlide]);

  // Mobil qurilmalar uchun surish (Swipe) funksiyasi
  const minSwipeDistance = 50;

  const onTouchStart = (e) => {
    setTouchEnd(null);
    setTouchStart(e.targetTouches[0].clientX);
  };

  const onTouchMove = (e) => {
    setTouchEnd(e.targetTouches[0].clientX);
  };

  const onTouchEndEvent = () => {
    if (touchStart === null || touchEnd === null) return;
    const distance = touchStart - touchEnd;

    if (distance > minSwipeDistance) nextSlide();
    if (distance < -minSwipeDistance) prevSlide();

    // holatni tozalaymiz, aks holda keyingi teginishda eski qiymat ishlatiladi
    setTouchStart(null);
    setTouchEnd(null);
  };

  // Slayd kontentini ko'rsatish
  const renderSlideContent = (slide) => {
    switch (slide.layout) {
      case 'title':
        return (
          <div className="flex flex-col items-center justify-center text-center h-full animate-fade-in-up">
            {slide.icon}
            <h1 className="text-5xl md:text-7xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500 mb-6 tracking-tight">
              {slide.title}
            </h1>
            <p className="text-xl md:text-3xl text-slate-300 font-light">
              {slide.subtitle}
            </p>
          </div>
        );
      case 'content':
        return (
          <div className="flex flex-col justify-center h-full max-w-4xl mx-auto animate-fade-in-up">
            {slide.icon}
            <h2 className="text-4xl md:text-6xl font-bold text-white mb-8 border-b border-slate-700 pb-4">
              {slide.title}
            </h2>
            <p className="text-xl md:text-2xl text-slate-300 leading-relaxed font-light">
              {slide.content}
            </p>
          </div>
        );
      case 'list':
        return (
          <div className="flex flex-col justify-center h-full max-w-4xl mx-auto animate-fade-in-up">
            {slide.icon}
            <h2 className="text-4xl md:text-6xl font-bold text-white mb-8 border-b border-slate-700 pb-4">
              {slide.title}
            </h2>
            <ul className="space-y-6">
              {slide.items.map((item, index) => (
                <li key={index} className="flex items-center text-xl md:text-3xl text-slate-300 font-light">
                  <span className="flex-shrink-0 w-3 h-3 rounded-full bg-blue-500 mr-4"></span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div
      className="relative w-full h-screen bg-slate-950 overflow-hidden flex flex-col font-sans selection:bg-blue-500 selection:text-white"
      onTouchStart={onTouchStart}
      onTouchMove={onTouchMove}
      onTouchEnd={onTouchEndEvent}
    >
      {/* Orqa fon bezaklari */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
        <div className="absolute -top-[20%] -left-[10%] w-[50%] h-[50%] rounded-full bg-blue-900/20 blur-[120px]"></div>
        <div className="absolute top-[60%] -right-[10%] w-[40%] h-[60%] rounded-full bg-purple-900/20 blur-[120px]"></div>
      </div>

      {/* Slayd Qismi — pastdagi panel ustiga tushmasligi uchun pb-24 */}
      <div className="flex-1 relative z-10 w-full h-full">
        {slides.map((slide, index) => (
          <div
            key={slide.id}
            className={`absolute inset-0 px-8 md:px-24 pb-24 transition-opacity duration-700 ease-in-out ${
              index === currentSlide ? 'opacity-100 pointer-events-auto z-20' : 'opacity-0 pointer-events-none z-0'
            }`}
          >
            {index === currentSlide && renderSlideContent(slide)}
          </div>
        ))}
      </div>

      {/* Boshqaruv tugmalari (Chap / O'ng) */}
      <button
        onClick={prevSlide}
        disabled={currentSlide === 0}
        className={`absolute left-4 top-1/2 -translate-y-1/2 p-3 rounded-full bg-white/10 hover:bg-white/20 text-white backdrop-blur-sm transition-all z-30 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
          currentSlide === 0 ? 'opacity-30 cursor-not-allowed' : 'opacity-100 cursor-pointer'
        }`}
        aria-label="Oldingi slayd"
      >
        <ChevronLeft className="w-8 h-8" />
      </button>

      <button
        onClick={nextSlide}
        disabled={currentSlide === lastIndex}
        className={`absolute right-4 top-1/2 -translate-y-1/2 p-3 rounded-full bg-white/10 hover:bg-white/20 text-white backdrop-blur-sm transition-all z-30 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
          currentSlide === lastIndex ? 'opacity-30 cursor-not-allowed' : 'opacity-100 cursor-pointer'
        }`}
        aria-label="Keyingi slayd"
      >
        <ChevronRight className="w-8 h-8" />
      </button>

      {/* Pastki qism - Jarayon (Progress) va Slayd Raqami */}
      <div className="absolute bottom-0 left-0 w-full z-30">
        <div className="flex justify-between items-center px-8 py-4 text-slate-400 text-sm font-medium">
          <span>Kompaniya Nomi / Ismingiz</span>
          <span>{currentSlide + 1} / {slides.length}</span>
        </div>
        {/* Progress Bar */}
        <div className="w-full h-1.5 bg-slate-800">
          <div
            className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-500 ease-out"
            style={{ width: `${((currentSlide + 1) / slides.length) * 100}%` }}
          ></div>
        </div>
      </div>

      {/*
        DIQQAT: <style jsx> — bu Next.js (styled-jsx) imkoniyati.
        Oddiy React (Vite / CRA) da u ishlamaydi va konsolda
        "Received `true` for a non-boolean attribute `jsx`" ogohlantirishi chiqadi.
        Shuning uchun oddiy <style> ishlatamiz.
      */}
      <style>{`
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(20px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in-up {
          animation: fadeInUp 0.8s ease-out forwards;
        }
      `}</style>
    </div>
  );
}
