import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { getProfileUrl } from '../../../utils/imageUtils';

const CastCard = ({ actor, index, showAllCast = false }) => {
  const navigate = useNavigate();

  const getCharacterName = member => {
    if (member.character) return member.character;
    if (member.main_character) return member.main_character;
    if (member.all_characters && member.all_characters.length > 0) {
      return member.all_characters[0];
    }
    return 'Actor';
  };

  const handleClick = () => {
    if (actor.id) {
      navigate(`/cast/${actor.id}`);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay: showAllCast ? index * 0.05 : index * 0.1 }}
      className="group relative overflow-hidden rounded-lg bg-gray-800 cursor-pointer transition-transform duration-300 hover:scale-105"
      onClick={handleClick}
    >
      <div className="aspect-[2/3] w-full overflow-hidden">
        <img
          src={getProfileUrl(actor, 'w500')}
          alt={actor.name || 'Actor'}
          className="size-full object-cover transition-transform duration-300 group-hover:scale-110"
          onError={e => {
            e.target.src = '/images/avatar_default.jpg';
          }}
        />
      </div>

      {/* Overlay with character info */}
      <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/90 via-black/50 to-transparent p-4">
        <h3 className="line-clamp-1 text-sm font-semibold text-white">
          {actor.name || 'Unknown Actor'}
        </h3>
        <p className="mt-1 line-clamp-1 text-xs text-gray-300">{getCharacterName(actor)}</p>

        {/* Hover effect - show "View Profile" */}
        <div className="absolute inset-0 flex items-center justify-center bg-black/80 opacity-0 transition-opacity duration-300 group-hover:opacity-100">
          <span className="text-sm font-medium text-white">View Profile</span>
        </div>
      </div>
    </motion.div>
  );
};

export default CastCard;
