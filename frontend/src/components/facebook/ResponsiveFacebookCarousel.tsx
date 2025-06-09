'use client';

import { Carousel } from '@/components/ui';
import { FacebookPost as FacebookPostType } from '@/types/facebook.type';
import FacebookPost from './FacebookPost';

interface ResponsiveFacebookCarouselProps {
  posts: FacebookPostType[];
  autoPlay?: boolean;
  truncateMessage?: boolean;
  maxMessageLength?: number;
  locale: string;
  profilePictureUrl?: string;
  translation: {
    unknownTime: string;
    post: string;
  };
}

// const useResponsiveItemsPerView = () => {
//   const [itemsPerView, setItemsPerView] = useState(3);

//   useEffect(() => {
//     const updateItemsPerView = () => {
//       const width = window.innerWidth;
//       if (width < 640) { // mobile
//         setItemsPerView(1);
//       } else if (width < 1024) { // tablet
//         setItemsPerView(2);
//       } else { // desktop
//         setItemsPerView(3);
//       }
//     };

//     updateItemsPerView();
//     window.addEventListener('resize', updateItemsPerView);
//     return () => window.removeEventListener('resize', updateItemsPerView);
//   }, []);

//   return itemsPerView;
// };

const ResponsiveFacebookCarousel: React.FC<ResponsiveFacebookCarouselProps> = ({
  posts,
  autoPlay = true,
  truncateMessage = true,
  maxMessageLength = 150,
  locale,
  translation,
  profilePictureUrl,
}) => {
//   const itemsPerView = useResponsiveItemsPerView();  
  return (
    <Carousel
      autoPlay={autoPlay}
      autoPlayInterval={6000}
      className="w-full"
      enableDrag={true}
      showDots={true}
    >
      {posts.map((post) => (
        <FacebookPost
          key={post.id}
          post={post}
          truncateMessage={truncateMessage}
          maxMessageLength={maxMessageLength}
          locale={locale}
          translation={translation}
          profilePictureUrl={profilePictureUrl}
        />
      ))}
    </Carousel>
  );
};

export default ResponsiveFacebookCarousel;
