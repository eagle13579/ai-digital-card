import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  Image,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  Linking,
  ActivityIndicator,
} from 'react-native';
import LoadingSpinner from '../components/LoadingSpinner';
import { apiGet } from '../api/client';

interface BusinessCard {
  id: string;
  name: string;
  company: string;
  title: string;
  phone: string;
  email: string;
  address?: string;
  website?: string;
  avatar?: string;
  bio?: string;
}

interface Props {
  route?: any;
  navigation?: any;
}

const CardDetailScreen: React.FC<Props> = ({ route, navigation }) => {
  const cardId = route?.params?.cardId;
  const [card, setCard] = useState<BusinessCard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!cardId) {
      setError('缺少名片ID');
      setLoading(false);
      return;
    }
    (async () => {
      try {
        const data = await apiGet<BusinessCard>(`/api/v1/cards/${cardId}`);
        setCard(data);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : '加载失败');
      } finally {
        setLoading(false);
      }
    })();
  }, [cardId]);

  const handleCall = (phone: string) => {
    Linking.openURL(`tel:${phone}`);
  };

  const handleEmail = (email: string) => {
    Linking.openURL(`mailto:${email}`);
  };

  const handleWebsite = (url: string) => {
    const href = url.startsWith('http') ? url : `https://${url}`;
    Linking.openURL(href);
  };

  if (loading) return <LoadingSpinner />;

  if (error || !card) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>{error || '名片不存在'}</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Avatar & Name */}
      <View style={styles.header}>
        {card.avatar ? (
          <Image source={{ uri: card.avatar }} style={styles.avatar} />
        ) : (
          <View style={[styles.avatar, styles.avatarPlaceholder]}>
            <Text style={styles.avatarInitial}>
              {card.name.charAt(0).toUpperCase()}
            </Text>
          </View>
        )}
        <Text style={styles.name}>{card.name}</Text>
        {card.title && <Text style={styles.title}>{card.title}</Text>}
        {card.company && <Text style={styles.company}>{card.company}</Text>}
      </View>

      {/* Bio */}
      {card.bio && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>简介</Text>
          <Text style={styles.bioText}>{card.bio}</Text>
        </View>
      )}

      {/* Contact Info */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>联系方式</Text>
        {card.phone && (
          <TouchableOpacity style={styles.contactRow} onPress={() => handleCall(card.phone!)}>
            <Text style={styles.contactLabel}>📞</Text>
            <Text style={styles.contactValue}>{card.phone}</Text>
          </TouchableOpacity>
        )}
        {card.email && (
          <TouchableOpacity style={styles.contactRow} onPress={() => handleEmail(card.email!)}>
            <Text style={styles.contactLabel}>📧</Text>
            <Text style={styles.contactValue}>{card.email}</Text>
          </TouchableOpacity>
        )}
        {card.website && (
          <TouchableOpacity style={styles.contactRow} onPress={() => handleWebsite(card.website!)}>
            <Text style={styles.contactLabel}>🌐</Text>
            <Text style={styles.contactValue}>{card.website}</Text>
          </TouchableOpacity>
        )}
        {card.address && (
          <View style={styles.contactRow}>
            <Text style={styles.contactLabel}>📍</Text>
            <Text style={styles.contactValue}>{card.address}</Text>
          </View>
        )}
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  content: {
    paddingBottom: 40,
  },
  header: {
    alignItems: 'center',
    paddingVertical: 32,
    backgroundColor: '#f8f9fa',
  },
  avatar: {
    width: 96,
    height: 96,
    borderRadius: 48,
    marginBottom: 16,
  },
  avatarPlaceholder: {
    backgroundColor: '#4a90d9',
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarInitial: {
    fontSize: 36,
    color: '#fff',
    fontWeight: '700',
  },
  name: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  title: {
    fontSize: 16,
    color: '#555',
    marginBottom: 2,
  },
  company: {
    fontSize: 14,
    color: '#888',
  },
  section: {
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  bioText: {
    fontSize: 15,
    color: '#555',
    lineHeight: 22,
  },
  contactRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
  },
  contactLabel: {
    fontSize: 18,
    width: 32,
  },
  contactValue: {
    fontSize: 16,
    color: '#333',
    flex: 1,
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorText: {
    fontSize: 16,
    color: '#e53935',
  },
});

export default CardDetailScreen;
