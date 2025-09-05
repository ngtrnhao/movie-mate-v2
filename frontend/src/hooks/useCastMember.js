import { useState, useEffect } from 'react';
import { getCastMemberDetail } from '../api/castService';

/**
 * Hook to manage cast member data
 * @param {number} castId - ID of the cast member
 * @returns {Object} cast member data, loading state, and error
 */
export const useCastMember = castId => {
  const [castMember, setCastMember] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchCastMember = async () => {
      if (!castId) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        const response = await getCastMemberDetail(castId);

        if (response.success) {
          setCastMember(response.cast_member);
        } else {
          setError(response.error);
        }
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to load cast member');
      } finally {
        setLoading(false);
      }
    };

    fetchCastMember();
  }, [castId]);

  return {
    castMember,
    loading,
    error,
    refetch: () => {
      setLoading(true);
      setError(null);
      const fetchCastMember = async () => {
        if (!castId) {
          setLoading(false);
          return;
        }

        try {
          setLoading(true);
          setError(null);
          const response = await getCastMemberDetail(castId);

          if (response.success) {
            setCastMember(response.cast_member);
          } else {
            setError(response.error);
          }
        } catch (err) {
          setError(err.response?.data?.error || 'Failed to load cast member');
        } finally {
          setLoading(false);
        }
      };

      fetchCastMember();
    },
  };
};
